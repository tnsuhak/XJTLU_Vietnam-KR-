from pathlib import Path

REPL={
    '도저':'쑤저우','도천':'쑤저우','도주':'쑤저우','토주':'쑤저우','주 · 상하이':'쑤저우 · 상하이',
    '시안 지아토נג-리버풀대학교':'시안교통리버풀대학교','시안 지아otong 리버풀대학교':'시안교통리버풀대학교',
    '시안 자이오팅 대학교':"Xi'an Jiaotong University",'시안 지아토נג 대학교':"Xi'an Jiaotong University",
    '시안 지아토ング-리버풀대학교':'시안교통리버풀대학교','지아토ング':'교통리버풀',
    '리버풀 대학':'리버풀대학교','학비과':'학비와','장학비':'장학금','입학학비':'입학 장학금',
    '학부금':'학비','국제학료':'국제학생 학비','학점은 연간':'학비는 연간','등록금: 연간 99,000원':'학비: 연간 99,000 RMB',
    '99,000만원':'99,000 RMB','99.000만원':'99.000 RMB','99,000원':'99,000 RMB','99.000원':'99.000 RMB',
    '후천 시립':'호치민시','TP 호치민':'호치민시','HCMG':'호치민시','HCM는':'호치민시는',
    '타이칸':'타이창','타이차':'타이창','중국어를 영어로':'영어로','중국 여행':'중국 유학',
    '자로 상담':'Zalo 상담','자로 메시지':'Zalo 메시지','브로체어':'브로셔','브로서':'브로셔','브로소':'브로셔',
    '조기동물':'Early Bird','초기 새':'Early Bird','조기 새':'Early Bird',
}
pages=sorted(Path('.').glob('*.html'))+sorted(Path('news').glob('*.html'))
for p in pages:
    text=p.read_text(encoding='utf-8')
    for a,b in REPL.items(): text=text.replace(a,b)
    p.write_text(text,encoding='utf-8')
print('global cleanup',len(pages))
