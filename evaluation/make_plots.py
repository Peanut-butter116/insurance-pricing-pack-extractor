import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd


def make(directory):
    for filename, dimension, output, title in [
        ('metrics_by_format.csv', 'format', 'comparison.png', 'Field accuracy by document format'),
        ('metrics_by_layout.csv', 'layout_group', 'layout_comparison.png', 'Generalisation to unseen layout D')]:
        data = pd.read_csv(directory / filename)
        split = 'test' if 'test' in data.split.values else 'development'
        data = data[data.split == split]
        pivot = data.pivot(index=dimension, columns='system', values='field_accuracy')
        order = [s for s in ['rules', 'slm', 'validated'] if s in pivot.columns]
        ax = (100 * pivot[order]).plot.bar(figsize=(9, 5), color=['#668096', '#2074b4', '#159680'][:len(order)], rot=0)
        ax.set(title=title + f' ({split})', ylabel='Correct fields (%)', xlabel='', ylim=(0, 112))
        for container in ax.containers:
            ax.bar_label(container, fmt='%.1f', fontsize=9)
        ax.legend(title='System', loc='upper right')
        ax.spines[['top', 'right']].set_visible(False)
        plt.figtext(.02, .01, 'Synthetic benchmark • Missing values included • No production performance claim', fontsize=9)
        plt.tight_layout(rect=(0, .04, 1, 1))
        plt.savefig(directory / output, dpi=170)
        plt.close()
