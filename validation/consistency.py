def warnings(values):
    issues = {}
    for field, value in values.items():
        if value is not None and not field.startswith('policy_') and field != 'rate_change_pct' and value < 0:
            issues[field] = 'negative value requires analyst review'
    if values['policy_start'] and values['policy_end'] and values['policy_end'] <= values['policy_start']:
        issues['policy_end'] = 'policy_end is not after policy_start'
    a, o = values['aggregate_limit_gbp'], values['occurrence_limit_gbp']
    if a is not None and o is not None and o > a:
        issues['occurrence_limit_gbp'] = 'occurrence limit exceeds aggregate limit'
    return issues
