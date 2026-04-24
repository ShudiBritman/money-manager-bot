import json
from .openai_service import ask_gpt

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

    try:
        return json.loads(response)
    except:
        return {"action": "unknown"}