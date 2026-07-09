import urllib.request

urls = ['http://localhost:8501/']
for u in urls:
    try:
        with urllib.request.urlopen(u, timeout=10) as r:
            body = r.read().decode('utf-8', errors='ignore')
            print('URL:', u)
            print('Status:', r.status)
            print('Length:', len(body))
            found = 'Screener' in body or 'screener' in body
            print('Contains "Screener" text?:', found)
            # print a short prefix
            print('Prefix snippet:', body[:400].replace('\n',' '))
    except Exception as e:
        print('Error fetching', u, e)
