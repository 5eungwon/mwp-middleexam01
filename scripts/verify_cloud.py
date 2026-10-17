"""Run live HTTPS API checks with a temporary photo; never print credentials."""
import argparse
import json,urllib.request,urllib.error,io
from pathlib import Path
from PIL import Image
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--base', default='https://asdfgh0986.pythonanywhere.com')
parser.add_argument('--credentials', required=True, type=Path, help='Private JSON containing username/password')
args=parser.parse_args()
BASE=args.base.rstrip('/')
assert BASE.startswith('https://'), 'Cloud verification requires HTTPS'
c=json.loads(args.credentials.read_text())
results=[]
def req(path,method='GET',data=None,token=None,ctype='application/json'):
 h={'Accept':'application/json'}
 if token:h['Authorization']='Token '+token
 if data is not None:
  if not isinstance(data,bytes):data=json.dumps(data).encode()
  h['Content-Type']=ctype
 try:
  with urllib.request.urlopen(urllib.request.Request(BASE+path,data=data,headers=h,method=method),timeout=60) as r:
   b=r.read();return r.status,json.loads(b) if 'json' in r.headers.get('Content-Type','') else b
 except urllib.error.HTTPError as e:return e.code,e.read().decode()[:400]
def check(label,actual,expected):
 assert actual==expected,(label,actual,expected)
 results.append({'check':label,'actual':actual,'expected':expected})
s,health=req('/api/health/');check('health',s,200);check('service',health['service'],'PhotoBlogServer')
s,arr=req('/api_root/Post/');check('lecture array',isinstance(arr,list),True);check('lecture HTTP',s,200)
s,page=req('/api/posts/');check('paginated API',s,200);check('pagination',isinstance(page['results'],list),True)
s,_=req('/api/posts/','POST',{'title':'anonymous'});check('anonymous write rejected',s,401)
s,login=req('/api/token/','POST',c);check('login',s,200);token=login['token']
b=io.BytesIO();Image.new('RGB',(1200,900),(68,113,94)).save(b,format='JPEG')
boundary='PhotoBlogCloudTestBoundary'
parts=[]
for key,value in [('title','클라우드 API 연동 검증'),('text','실제 HTTPS 서버의 업로드·수정·삭제 검증')]:parts.append(('--'+boundary+'\r\nContent-Disposition: form-data; name="'+key+'"\r\n\r\n'+value+'\r\n').encode())
parts.append(('--'+boundary+'\r\nContent-Disposition: form-data; name="image"; filename="cloud-test.jpg"\r\nContent-Type: image/jpeg\r\n\r\n').encode()+b.getvalue()+b'\r\n')
body=b''.join(parts)+('--'+boundary+'--\r\n').encode()
s,post=req('/api/posts/','POST',body,token,'multipart/form-data; boundary='+boundary);check('multipart upload',s,201)
path='/api/posts/'+str(post['id'])+'/'
s,_=req(post['image'].removeprefix(BASE));check('uploaded image GET',s,200)
s,p=req(path,'PATCH',{'title':'클라우드 수정 확인'},token);check('PATCH',s,200);check('updated title',p['title'],'클라우드 수정 확인')
s,_=req(path,'DELETE',token=token);check('DELETE',s,204)
s,_=req(path);check('deleted post',s,404)
Path('docs/evidence/12-cloud-api-verification.json').write_text(json.dumps({'server':BASE,'health':health,'server_redeployed':True,'checks':results},ensure_ascii=False,indent=2))
print(json.dumps({'server':BASE,'passed':len(results),'health':health},ensure_ascii=False))
