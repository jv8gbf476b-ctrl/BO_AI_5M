"""
BO_AI_5M v6
report.py
"""

from history import load_history


def trade_df(df):
    return df[df["result"] != "NO_TRADE"] if not df.empty else df


def calc_win_rate(df):
    df = trade_df(df)
    if df.empty:
        return 0,0,0,0.0
    total=len(df)
    wins=len(df[df["result"]=="WIN"])
    losses=len(df[df["result"]=="LOSE"])
    return total,wins,losses,wins/total*100


def make_report_text():
    df=load_history()
    if df.empty:
        return "📊 成績: まだ記録なし"

    total,wins,losses,rate=calc_win_rate(df)
    skip=len(df[df["result"]=="NO_TRADE"])

    txt=f"""📊 BO_AI_5M 成績

累計エントリー : {total}戦
勝ち : {wins}
負け : {losses}
勝率 : {rate:.1f}%
見送り : {skip}回

"""

    for sig in ["HIGH","LOW"]:
        s=df[df["signal"]==sig]
        t,w,l,r=calc_win_rate(s)
        if t:
            txt+=f"{sig} : {t}戦 {w}勝 {l}敗 ({r:.1f}%)\n"

    return txt
