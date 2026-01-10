# PythonAnywhere Scheduled Task Setup

## Issue: Scheduled task se emails nahi aa rahi

### Solution:

1. **Scheduled Task Verify Karo:**

PythonAnywhere Dashboard → **Tasks** tab:

- Task enabled hai? ✅
- Last run time kya hai?
- Output/errors check karo

2. **Correct Command:**

```bash
cd /home/a3dcreator/wildwood-backend && /home/a3dcreator/wildwood-backend/env/bin/python manage.py send_abandoned_cart_emails
```

*(Replace `a3dcreator` with your PythonAnywhere username)*

3. **Frequency:**

For testing: `*/2 * * * *` (every 2 minutes)
For production: `0 * * * *` (every hour)

4. **Check Logs:**

PythonAnywhere console mein:
```bash
cd ~/wildwood-backend
tail -f logs/error.log
```

Ya check scheduled task output in Tasks tab.

5. **Manual Test:**

```bash
python manage.py check_abandoned_carts
python manage.py send_abandoned_cart_emails
```

## Common Issues:

### Issue 1: Task not running
- Check task is enabled
- Check command path is correct
- Check cron syntax is correct

### Issue 2: Task running but no emails
- Run `check_abandoned_carts` to see if carts are ready
- Check email settings in `.env`
- Check error logs

### Issue 3: Timezone mismatch
- PythonAnywhere uses UTC
- Check `USE_TZ = True` in settings.py
- Scheduler uses `timezone.now()` which handles timezone automatically

