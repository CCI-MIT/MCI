def forPresentation(summaries, subjects):
    if not summaries:
        return None
    seidsInOrder = [s[0] for s in summaries if s[0] != 'Totals']
    def sidForSeid(seid):
        l = [sub.pk for sub in subjects if sub.external_id == seid]
        return l[0]
    def withInteractionStatsAsList(summary):
        sidsInOrder = map(lambda seid: str(sidForSeid(seid)), seidsInOrder)
        if summary[0] != "Totals":
            summary[1]['interactions'] = map(
                lambda sid: summary[1]['interactions'][sid],
                sidsInOrder
            )
        return summary
        
    return [withInteractionStatsAsList(s) for s in summaries]

def listWithTotalsLast(d, task_type, subs):
    if not d:
        return None
    if not 'Totals' in d:
        return sorted(d.items())
    totals = d['Totals']
    l = [(k, v) for k, v in sorted(d.items()) if k != 'Totals'] + [('Totals', totals)]
    return forPresentation(l, subs) if task_type == 'S' else l
