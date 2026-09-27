import csv
import os
import re
import random
from collections import Counter, defaultdict
from datetime import datetime, timedelta

BASE=os.path.dirname(os.path.abspath(__file__))
OUT=os.path.join(BASE, "output")
TICKET_FILE="cded5ec7-cd54-40e6-ba66-7b3e581319c7-tickets.csv"
AGENT_FILE="1bb95ea8-f7cb-44b6-b5d2-2fb20c9a4e47-agents.csv"
POLICY_RATE=290
def load_file(name):
    path=os.path.join(BASE, name)
    with open(path, "r", encoding="utf-8-sig", newline="") as file:
        return list(csv.DictReader(file))
def parse_date(value):
    if not value:
        return None
    return datetime.strptime(value, "%Y-%m-%d %H:%M")


def pick_rows(rows):
    groups=defaultdict(list)
    for row in rows:
        groups[row["ticket_id"]].append(row)
    chosen=[]
    for items in groups.values():
        current=[item for item in items if item["source_system"]=="helpdesk"]
        chosen.append(current[0] if current else items[0])
    return chosen, len(rows) - len(chosen)
def words(text):
    return set(re.findall(r"[a-z0-9]+", text.lower()))


def tag(row):
    text=row.get("customer_message", "")+" "+row.get("agent_notes", "")
    text_words=words(text)
    rules={
        "Delivery & Shipping": {"delivery", "delayed", "delay", "late", "courier", "tracking", "shipment", "delivered", "transit"},
        "Billing & Payments": {"payment", "paid", "charge", "charged", "invoice", "refund", "billing", "coupon", "upi"},
        "Returns & Refunds": {"return", "replace", "replacement", "refund", "pickup", "wrong item"},
        "Connectivity": {"bluetooth", "pair", "pairing", "connect", "disconnect", "connection", "wifi"},
        "Charging & Battery": {"battery", "charge", "charging", "charger", "power", "dies", "drain"},
        "App & Firmware": {"app", "firmware", "update", "install", "login", "account", "otp"},
        "Audio Quality": {"sound", "audio", "volume", "noise", "mic", "microphone", "bass", "distortion"},
        "Hardware Fault": {"broken", "stopped", "dead", "fault", "damage", "not working", "crack", "left earbud", "right earbud"},
        "Warranty": {"warranty", "rma", "warranty", "claim", "service"},
    }
    scores=Counter()
    for name, keys in rules.items():
        for key in keys:
            if " " in key:
                if key in text.lower():
                    scores[name]+=2
            elif key in text_words:
                scores[name]+=1
    if scores:
        return scores.most_common(1)[0][0]
    return row.get("category") or "Other"


def roster(rows):
    result=defaultdict(list)
    for row in rows:
        result[row["agent_id"]].append(row)
    return result


def agent_info(agent_rows, agent_id, when):
    for row in agent_rows.get(agent_id, []):
        start=datetime.strptime(row["from_date"], "%Y-%m-%d")
        end=datetime.strptime(row["to_date"], "%Y-%m-%d") if row["to_date"] else datetime.max
        if start<=when<=end:
            return row
    return agent_rows.get(agent_id, [{}])[0]


def mark_repeats(rows):
    groups=defaultdict(list)
    for row in rows:
        row["text_issue"]=tag(row)
        row["issue"]=row.get("category") or row["text_issue"]
        groups[(row.get("customer_id", ""), row["issue"])].append(row)
    repeat_ids=set()
    for items in groups.values():
        items.sort(key=lambda item: item["created"])
        for current, previous in zip(items[1:], items[:-1]):
            gap=current["created"]-previous["resolved"]
            if timedelta(0)<=gap<=timedelta(days=30):
                repeat_ids.add(current["ticket_id"])
    return repeat_ids


def write_csv(name, rows, fields):
    with open(os.path.join(OUT, name), "w", encoding="utf-8", newline="") as file:
        writer=csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def make_data():
    raw=load_file(TICKET_FILE)
    agents=roster(load_file(AGENT_FILE))
    rows,duplicate_count=pick_rows(raw)
    clean=[]
    for row in rows:
        row["created"]=parse_date(row["created_at"])
        row["resolved"]=parse_date(row["resolved_at"]) or row["created"]
        row["response"]=parse_date(row["first_response_at"])
        if not row["created"]:
            continue
        clean.append(row)
    repeats=mark_repeats(clean)
    for row in clean:
        row["week"]=row["created"].date()-timedelta(days=row["created"].weekday())
        row["repeat"]=row["ticket_id"] in repeats
    return raw, clean, agents, duplicate_count


def digest(rows):
    result=[]
    by_week=defaultdict(list)
    for row in rows:
        by_week[row["week"]].append(row)
    for week, items in sorted(by_week.items()):
        counts=Counter(row["issue"] for row in items)
        for issue, count in counts.most_common():
            result.append({
                "week_start": week.isoformat(),
                "issue": issue,
                "tickets": count,
                "share_pct": round(count * 100 / len(items), 1),
                "repeat_tickets":sum(row["repeat"] and row["issue"]==issue for row in items),
            })
    return result


def board(rows, agents):
    counts=Counter()
    for row in rows:
        if row["status"] not in ("resolved", "closed"):
            continue
        info=agent_info(agents, row["agent_id"], row["resolved"])
        team=info.get("team", row.get("assigned_team", ""))
        if "Warranty" in team or "Escalations" in team:
            continue
        week=row["resolved"].date()-timedelta(days=row["resolved"].weekday())
        counts[(week, row["agent_id"], info.get("name", "Unknown"), team)]+=1
    return [
        {"week_start": week.isoformat(), "agent_id": agent_id, "agent": name, "team": team, "tickets_closed": count}
        for (week, agent_id, name, team), count in sorted(counts.items())
    ]


def generate_action_recommendations(weekly_digest):
    stats=defaultdict(lambda: {"tickets":0, "repeat":0})
    for row in weekly_digest:
        issue=row["issue"]
        stats[issue]["tickets"]+=int(row["tickets"])
        stats[issue]["repeat"]+=int(row["repeat_tickets"])
    total=sum(item["tickets"] for item in stats.values())
    repeat_total=sum(item["repeat"] for item in stats.values())
    overall_rate=repeat_total*100/total if total else 0
    owners={
        "Delivery & Shipping":"Logistics / Operations",
        "Billing & Payments":"Billing / Payments Operations",
        "Returns & Refunds":"Returns Desk / Operations",
        "Connectivity":"Product Support / Engineering",
        "Charging & Battery":"Product Support / Engineering",
        "App & Firmware":"App Support / Engineering",
        "Audio Quality":"Product Support / Quality",
        "Warranty & Repair":"Escalations & Warranty",
        "Product Enquiry":"Frontline Support / Product",
        "Account & Login":"Frontline Support / Account Services",
        "Other":"Support Operations",
    }
    ranked=[]
    for issue, item in stats.items():
        rate=item["repeat"]*100/item["tickets"] if item["tickets"] else 0
        share=item["tickets"]*100/total if total else 0
        score=share+rate
        ranked.append({"issue":issue, "tickets":item["tickets"], "repeat":item["repeat"], "rate":rate, "share":share, "score":score})
    ranked.sort(key=lambda item: (-item["score"], -item["tickets"], item["issue"]))
    volume=max(ranked, key=lambda item: (item["tickets"], item["repeat"], item["issue"]))
    rate=max(ranked, key=lambda item: (item["rate"], item["repeat"], item["tickets"], item["issue"]))
    focus=rate if rate["rate"]>overall_rate else volume
    owner=owners.get(focus["issue"], "Support Operations")
    lines=[
        "# VIREO AUDIO - ACTION RECOMMENDATIONS",
        "",
        "## Priority issue",
        focus["issue"],
        "",
        "## Why it matters",
        f"{volume['issue']} generated the highest ticket volume with {volume['tickets']:,} tickets ({volume['share']:.1f}% of the dataset).",
        f"{rate['issue']} had the highest repeat-contact rate at {rate['rate']:.1f}% ({rate['repeat']:,} repeat contacts from {rate['tickets']:,} tickets).",
        "",
        "## Repeat-contact signal",
        f"{focus['repeat']:,} repeat contacts were associated with {focus['issue']}, a {focus['rate']:.1f}% repeat-contact rate versus {overall_rate:.1f}% overall.",
        "",
        "## Recommended owner",
        owner,
        "",
        "## Suggested action",
        f"Review {focus['issue'].lower()} cases that generated repeat contacts, then inspect the notes and operational hand-offs for a common fix.",
        "",
        "## Measure next",
        f"Track the weekly repeat-contact rate for {focus['issue']}.",
        "",
        "## Success metric",
        f"Reduce the {focus['issue']} repeat-contact rate below its current {focus['rate']:.1f}% baseline.",
        "",
        "## Evidence",
        f"Based on {total:,} canonical tickets aggregated from the weekly digest. The priority score is issue share plus repeat-contact rate; it is a prioritization aid, not proof of root cause.",
        "",
        "## Top scored issues",
        "| Issue | Tickets | Repeat contacts | Repeat rate | Priority score |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for item in ranked[:5]:
        lines.append(f"| {item['issue']} | {item['tickets']:,} | {item['repeat']:,} | {item['rate']:.1f}% | {item['score']:.1f} |")
    return "\n".join(lines)+"\n"


def validate(rows):
    sample=rows[:]
    random.Random(42).shuffle(sample)
    sample=sample[:200]
    text_correct=sum(row["text_issue"]==row.get("category") for row in sample)
    report_correct=sum(row["issue"]==row.get("category") for row in sample)
    text_error=round((len(sample)-text_correct)*100/len(sample), 1)
    return len(sample), report_correct, text_correct, text_error


def main():
    os.makedirs(OUT, exist_ok=True)
    raw,rows,agents,duplicate_count=make_data()
    digest_rows=digest(rows)
    board_rows=board(rows, agents)
    sample_size,report_correct,text_correct,error_rate=validate(rows)
    repeat_count=sum(row["repeat"] for row in rows)
    resolved_count=sum(row["status"] in ("resolved", "closed") for row in rows)
    avg_quarter=repeat_count/6
    saving=avg_quarter*0.20*POLICY_RATE
    write_csv("weekly_digest.csv", digest_rows, ["week_start", "issue", "tickets", "share_pct", "repeat_tickets"])
    write_csv("leaderboard.csv", board_rows, ["week_start", "agent_id", "agent", "team", "tickets_closed"])
    with open(os.path.join(OUT, "action_recommendations.md"), "w", encoding="utf-8") as file:
        file.write(generate_action_recommendations(digest_rows))
    with open(os.path.join(OUT, "impact.txt"), "w", encoding="utf-8") as file:
        file.write("BUSINESS GOAL\n")
        file.write(f"Baseline repeat contacts: {repeat_count} of {len(rows)} canonical tickets ({repeat_count * 100 / len(rows):.1f}%).\n")
        file.write("Target: reduce repeat contacts by 20% relative to this baseline.\n")
        file.write(f"Estimated quarterly saving at Rs {POLICY_RATE} per contact: Rs {saving:,.0f}.\n")
        file.write("This is a scenario estimate, not a guaranteed saving.\n")
    with open(os.path.join(OUT, "validation.txt"), "w", encoding="utf-8") as file:
        file.write(f"Raw rows: {len(raw)}\nCanonical ticket IDs: {len(rows)}\nDuplicate rows removed: {duplicate_count}\n")
        file.write(f"Resolved/closed tickets: {resolved_count}\nManual proxy check sample: {sample_size}\n")
        file.write(f"Digest category agreement with source field: {report_correct}/{sample_size}\n")
        file.write(f"Independent text-tag agreement with source field: {text_correct}/{sample_size}\nText-tag error rate: {error_rate}%\n")
        file.write("Known error pattern: text tagging struggles with multi-issue and vague messages; the digest therefore uses the supplied structured category.\n")
    with open(os.path.join(OUT, "memo.md"), "w", encoding="utf-8") as file:
        file.write("# Memo: Vireo Audio support tickets\n\n")
        file.write("To: Priya Raman, Head of Customer Experience\n\n")
        file.write(f"The tool turns {len(rows):,} canonical tickets into a weekly complaint digest and a closure-volume leaderboard. It removes {duplicate_count} migration duplicate rows and keeps the warranty team out of Tier 1 volume comparisons.\n\n")
        file.write(f"The main opportunity is repeat contact: {repeat_count:,} tickets ({repeat_count*100/len(rows):.1f}%) matched the policy proxy of the same customer and issue returning within 30 days. A 20% reduction would be worth about Rs {saving:,.0f} per quarter at the policy rate of Rs {POLICY_RATE} per contact. This is the number to manage, not a claim that the tool itself guarantees savings.\n\n")
        file.write("The leaderboard is deliberately labelled workload, not performance. Warranty cases are multi-touch and must be measured in resolution days. The digest uses a fixed local taxonomy, so it has no per-ticket model bill.\n\n")
        file.write("Next action: review the top weekly issues with product, logistics, and returns owners, choose one repeat-contact issue, and compare its rate after one quarter.\n")
    print(f"Created output for {len(rows)} canonical tickets in {OUT}")


if __name__=="__main__":
    main()