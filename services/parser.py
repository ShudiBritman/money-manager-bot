import json
from .openai_service import ask_gpt

MONTHS = [
    "ינואר","פברואר","מרץ","אפריל","מאי","יוני",
    "יולי","אוגוסט","ספטמבר","אוקטובר","נובמבר","דצמבר"
]

def detect_month(text):
    for m in MONTHS:
        if m in text:
            return m
    return None 


def parse_message(text):
    messages = [
    {
        "role": "system",
        "content": """
אתה מערכת לניהול הוצאות.

תחזיר JSON בלבד.

פעולות:

1. הוספת הוצאה:
{
 "action": "add_expense",
 "amount": number,
 "category": "בגדים |בלתי צפוי | אוכל | תחבורה | דיור | חשבונות | כללי | אוכל בחוץ"
 "description": string
}

2. הוספת הוצאה קבועה:
{
 "action": "add_fixed_expense",
 "amount": number,
 "category": "אוכל | תחבורה | דיור | בגדים | חשבונות | בלתי צפוי | כללי | אוכל בחוץ",
 "description": string
}

3. סיכום חודשי:
{
 "action": "get_summary"
}

4. סיכום לפי קטגוריה:
{
 "action": "get_category",
 "category": string
}

5. מחיקת הוצאה:
{
 "action": "delete_last"
}

6. הגדרת תקציב כללי:
{
 "action": "set_total_budget",
 "amount": number
}

7. הגדרת תקציב קטגוריה:
{
 "action": "set_category_budget",
 "category": string,
 "amount": number
}

8. כמה נשאר כללי:
{
 "action": "remaining_total"
}

9. כמה נשאר בקטגוריה:
{
 "action": "remaining_category",
 "category": string
}

10. לא מובן:
{
 "action": "unknown"
}

10. איפוס נתונים:
{
 "action": "reset"
}
11. הצגת הוצאות קבועות:
{
 "action": "get_fixed_expenses"
}
12. איפוס הוצאות קבועות:
{
 "action": "reset_fixed_expenses"
}
13. סיכום לפי חודש:
{
 "action": "get_month_summary",
 "month": "שם חודש בעברית",
 "category": "אופציונלי"
}

חוקים:
- להבין עברית חופשית
- לזהות סכומים גם בתוך משפט
- לבחור קטגוריה מתאימה
- לזהות משפטים כמו "התקציב שלי 5000"
- לזהות "כמה נשאר לי"
- להבין "תקציב אוכל 1500"
- להבין "כמה נשאר לי באוכל"
- תמיד להחזיר JSON בלבד
"""
    },
    {"role": "user", "content": text}
]

    response = ask_gpt(messages)

    if not response:
        return {"action": "unknown"}

    response = response.strip()

    if response.startswith("```"):
        response = response.split("```")[1]

    response = response.replace("json", "").strip()

    try:
        data = json.loads(response)
    except Exception as e:
        print("❌ JSON ERROR:", response, e)
        return {"action": "unknown"}

    if not data or "action" not in data:
        print("❌ INVALID DATA:", data)
        return {"action": "unknown"}

    # זיהוי חודש רק לסיכומים
    month = detect_month(text)

    if month and data.get("action") == "get_summary":
        return {
            "action": "get_month_summary",
            "month": month,
            "category": data.get("category")
        }

    return data
    

