# coding=utf-8
from Pix_Chan import PixAI
import time
import traceback
from settings import accounts,proxies

for account in accounts:
    try:
        print([account["email"], account["password"]])
        pix = PixAI(account["email"], account["password"], login=True, proxy=proxies)
        pix.claim_daily_quota()
        time.sleep(5)
    except Exception as e:
        print(e)
        print(traceback.format_tb(e.__traceback__))