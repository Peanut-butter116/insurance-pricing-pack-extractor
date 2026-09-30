import os
import time
import platform
from config import SEED


class SLMBackend:
    def __init__(self):
        import torch
        from transformers import AutoTokenizer, AutoModelForCausalLM, set_seed
        set_seed(SEED)
        torch.set_num_threads(min(4, os.cpu_count() or 1))
        self.model_id = os.getenv('MODEL_ID', 'Qwen/Qwen2.5-1.5B-Instruct')
        revision = os.getenv('MODEL_REVISION') or ('989aa7980e4cf806f80c7fef2b1adb7bc71aa306' if self.model_id == 'Qwen/Qwen2.5-1.5B-Instruct' else 'main')
        requested = os.getenv('SLM_DEVICE', 'auto')
        self.device = ('cuda' if torch.cuda.is_available() else 'mps' if torch.backends.mps.is_available() else 'cpu') if requested == 'auto' else requested
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_id, revision=revision)
        self.model = AutoModelForCausalLM.from_pretrained(self.model_id, revision=revision,
            dtype=torch.float32 if self.device == 'cpu' else torch.float16).to(self.device).eval()
        self.metadata = {'model_id': self.model_id, 'revision': getattr(self.model.config, '_commit_hash', revision),
                         'device': self.device, 'platform': platform.platform(), 'processor': platform.processor(),
                         'torch': torch.__version__, 'seed': SEED, 'do_sample': False, 'max_new_tokens': 1200,
                         'dtype': str(self.model.dtype), 'parameters': self.model.num_parameters()}

    def generate(self, system, payload):
        import torch
        messages = [{'role': 'system', 'content': system}, {'role': 'user', 'content': payload}]
        prompt = self.tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        inputs = self.tokenizer(prompt, return_tensors='pt').to(self.device)
        if inputs.input_ids.shape[1] > 24000:
            raise ValueError('Document exceeds pilot context limit; no silent truncation')
        start = time.perf_counter()
        with torch.inference_mode():
            out = self.model.generate(**inputs, do_sample=False, max_new_tokens=1200, pad_token_id=self.tokenizer.eos_token_id)
        raw = self.tokenizer.decode(out[0, inputs.input_ids.shape[1]:], skip_special_tokens=True)
        return raw, {'seconds': time.perf_counter() - start, 'input_tokens': int(inputs.input_ids.shape[1]),
                     'output_tokens': int(out.shape[1] - inputs.input_ids.shape[1])}
