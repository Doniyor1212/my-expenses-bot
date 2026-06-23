from .ai_utils import progress_bar


def calculate_score(total_growth, increased_count, impulse_count, optimizable_total, total_current):
    score = 10.0

    if total_growth is not None:
        if total_growth > 70:
            score -= 3
        elif total_growth > 40:
            score -= 2
        elif total_growth > 15:
            score -= 1

    if increased_count >= 5:
        score -= 2
    elif increased_count >= 3:
        score -= 1

    if impulse_count >= 3:
        score -= 1.5
    elif impulse_count >= 1:
        score -= 0.5

    if total_current > 0:
        optimizable_share = optimizable_total / total_current * 100
        if optimizable_share > 55:
            score -= 1.5
        elif optimizable_share > 35:
            score -= 0.8

    if score < 1:
        score = 1

    return round(score, 1)


def build_score_text(score):
    if score >= 8:
        comment = "👍 Отличный результат"
    elif score >= 6:
        comment = "👌 Нормально, но есть потенциал экономии"
    elif score >= 4:
        comment = "⚠️ Расходы требуют контроля"
    else:
        comment = "🚨 Высокий риск перерасхода"

    return (
        "🏆 Финансовая дисциплина\n\n"
        f"{progress_bar(score)}\n"
        f"{score} / 10\n\n"
        f"{comment}"
    )
