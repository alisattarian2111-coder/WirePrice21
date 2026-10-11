#!/usr/bin/env python3
"""Best-effort daily public price-list collector. Keeps source/date and avoids inventing prices."""
import json, re, time, urllib.request, urllib.error
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'prices.json'
SOURCES=[
 {'name':'برق‌سان · افشارنژاد','brand':'خراسان افشارنژاد','url':'https://www.barghsan.com/%D9%84%DB%8C%D8%B3%D8%AA-%D9%82%DB%8C%D9%85%D8%AA-%D8%B3%DB%8C%D9%85-%D9%88-%DA%A9%D8%A7%D8%A8%D9%84-%D8%AE%D8%B1%D8%A7%D8%B3%D8%A7%D9%86-%D8%A7%D9%81%D8%B4%D8%A7%D8%B1%D9%86%DA%98%D8%A7%D8%AF/'},
 {'name':'برق‌سان · سیمیا','brand':'سیمیا','url':'https://www.barghsan.com/simia-price-list/'},
 {'name':'پرتو الکتریک','brand':'پرتو الکتریک','url':'https://parto-electric.com/'},
 {'name':'راندنو · سیم و کابل','brand':'متنوع','url':'https://randeno.com/itemslist/wire-and-cable'},
 {'name':'کابل ایران · لیست همکاری','brand':'متنوع','url':'https://cableiran.com/content/6-price-list'},
]
class TextParser(HTMLParser):
 def __init__(self): super().__init__();self.parts=[];self.skip=0
 def handle_starttag(self,tag,attrs):
  if tag in ('script','style','noscript','svg'):self.skip+=1
  if tag in ('tr','td','th','li','p','br','h1','h2','h3','div'):self.parts.append('\n')
 def handle_endtag(self,tag):
  if tag in ('script','style','noscript','svg') and self.skip:self.skip-=1
  if tag in ('tr','td','th','li','p','br','h1','h2','h3','div'):self.parts.append('\n')
 def handle_data(self,data):
  if not self.skip:self.parts.append(data)
 def text(self):return re.sub(r'[ \t\xa0]+',' ',' '.join(self.parts)).replace('\r','')
def get_page(url):
 req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0 (compatible; WirePriceBot/1.0; public price-list reader)'})
 with urllib.request.urlopen(req,timeout=25) as r:return r.read().decode('utf-8','replace')
def digits(s):
 trans=str.maketrans('۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩٬٫','01234567890123456789,.')
 return s.translate(trans)
def clean(s):
 s=digits(s);s=re.sub(r'\s+',' ',s);return s.strip(' |\t-:')
def parse_source(src):
 html=get_page(src['url']);p=TextParser();p.feed(html);txt=p.text()
 # Use line-level records to reduce false positives. Sources commonly render a product row and price together.
 lines=[clean(x) for x in txt.splitlines() if clean(x)]
 out=[];seen=set()
 for line in lines:
  if len(line)>240 or not re.search(r'\b(سیم|کابل)\b',line):continue
  if not re.search(r'\d',line):continue
  if any(x in line.lower() for x in ('تعداد فروشندگان','لیست قیمت','به روزرسانی','به‌روزرسانی','دانلود لیست','تماس حاصل','مشاهده قیمت')):continue
  # Require a clear price separator or a table-like row, and a plausible final numeric amount.
  nums=re.findall(r'(?<![\w])\d[\d,.]*(?![\w])',line)
  if len(nums)<2:continue
  raw=nums[-1].replace(',','').replace('.','')
  try:price=int(raw)
  except ValueError:continue
  if price<1000 or price>10_000_000_000:continue
  # Price-list pages usually have a pipe, or source text includes a currency/unit after product.
  if not ('|' in line or 'تومان' in line or 'ریال' in line or re.search(r'\d\s{1,}\d{3}',line)):continue
  product=line
  product=re.sub(r'\|.*$','',product).strip()
  product=re.sub(r'\b\d[\d,.]*\s*(تومان|ریال)\b','',product).strip()
  product=re.sub(r'\s{2,}',' ',product)
  if len(product)<6:continue
  brand=src['brand']
  for b in ['افشارنژاد','خراسان','سیمیا','کمان','پرتو الکتریک','رسا','راد افشان سحر','سهند','دامغان','همدان','زر کابل کرمان','رفسنجان','تک سیم البرز','البرز الکتریک نور','مغان','آمل','سیمند کابل']:
   if b in line:brand=b if b!='افشارنژاد' else 'خراسان افشارنژاد';break
  kind='سیم' if 'سیم' in product and 'کابل' not in product else 'کابل'
  unit='متر' if 'متر' in line else ('حلقه' if 'حلقه' in line else '')
  key=(product,brand,price,src['name'])
  if key in seen:continue
  seen.add(key);out.append({'product':product,'brand':brand,'kind':kind,'category':'قیمت منتشرشده','price':price,'currency':'تومان','unit':unit,'source':src['name'],'url':src['url'],'date':datetime.now(timezone.utc).astimezone().strftime('%Y-%m-%d'),'status':'استخراج خودکار؛ تأیید منبع لازم است'})
 return out

def main():
 old={}
 if OUT.exists():
  try:old=json.loads(OUT.read_text(encoding='utf-8'))
  except Exception:pass
 all_items=[];source_status=[]
 for src in SOURCES:
  try:
   rows=parse_source(src);all_items.extend(rows);source_status.append({'name':src['name'],'url':src['url'],'ok':True,'items':len(rows)})
   print(f"OK {src['name']}: {len(rows)} rows")
  except Exception as e:
   source_status.append({'name':src['name'],'url':src['url'],'ok':False,'items':0,'error':str(e)[:180]})
   print(f"WARN {src['name']}: {e}")
  time.sleep(1)
 # Preserve last successful source records if a source temporarily fails, but mark their old date as-is.
 successful={s['name'] for s in source_status if s['ok']}
 for item in old.get('items',[]):
  if item.get('source') not in successful:all_items.append(item)
 # Deduplicate exact records and sort by product.
 unique={}
 for x in all_items:unique[(x.get('product'),x.get('brand'),x.get('price'),x.get('source'))]=x
 payload={'checked_at':datetime.now(timezone.utc).isoformat(),'items':sorted(unique.values(),key=lambda x:(x.get('product',''),x.get('brand',''),x.get('source',''))),'sources':source_status,'note':'Source pages are public price lists; scraped prices may be list/wholesale prices and must be verified with the seller.'}
 OUT.write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding='utf-8')
 print(f"Wrote {len(payload['items'])} items to {OUT}")
if __name__=='__main__':main()
