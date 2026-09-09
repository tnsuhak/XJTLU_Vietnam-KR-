from __future__ import annotations

from pathlib import Path
from bs4 import BeautifulSoup, Comment, NavigableString
import re, shutil, sys

SOURCE = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path('/tmp/xjtlu-vietnam-source')
ROOT = Path('.')
PROD_HOST = 'https://xjtlu-vietnam.netlify.app'
REVIEW_HOST = 'https://xjtlu-vietnam-kr.netlify.app'
NEW_PAGES = [
    'xjtlu-chi-phi-sinh-hoat-2027.html',
    'xjtlu-ky-tuc-xa-sip-taicang.html',
    'xjtlu-to-chau-thuong-hai-viet-nam.html',
]

COMMON = {
    'XJTLU Việt Nam':'XJTLU 베트남', 'XJTLU VIỆT NAM':'XJTLU 베트남', 'Menu':'메뉴', 'Menu ☰':'메뉴 ☰',
    'Trang chính và các hướng dẫn chi tiết được nhóm theo chủ đề.':'메인 페이지와 상세 가이드를 주제별로 모았습니다.',
    'Giới thiệu XJTLU':'XJTLU 소개', 'Trang chính':'메인', 'Trang chính →':'메인 →',
    'Bằng University of Liverpool & lộ trình 2+2':'리버풀대학교 학위 & 2+2 경로',
    'Bằng University of Liverpool & 2+2':'리버풀대학교 학위 & 2+2',
    'Liverpool & Việt Nam':'Liverpool & 베트남', 'Tô Châu, Thượng Hải & Việt Nam':'쑤저우·상하이 & 베트남',
    'Ngành học & nghề nghiệp':'전공 & 진로', 'Xem chi tiết →':'자세히 보기 →',
    'Ngành học, nghề nghiệp & lựa chọn chương trình':'전공, 진로 & 프로그램 선택',
    'Kết quả học lên sau tốt nghiệp':'졸업 후 진학 결과', 'Học phí & học bổng':'학비 & 장학금',
    'Học phí, học bổng & các mốc quan trọng 2027':'학비, 장학금 & 2027 주요 일정',
    'Học phí & ngân sách':'학비 & 예산', 'Học phí & học bổng 2027':'2027 학비 & 장학금',
    'Chi phí sinh hoạt XJTLU 2027':'XJTLU 생활비 2027', 'Đời sống sinh viên':'학생 생활',
    'Thể thao & cơ sở thể thao':'스포츠 & 체육시설', 'Câu lạc bộ & tổ chức sinh viên':'동아리 & 학생단체',
    'Video đời sống XJTLU':'XJTLU 학생생활 영상', 'Thể thao, CLB & video':'스포츠, 동아리 & 영상',
    'Ký túc xá SIP & Taicang':'SIP & 타이창 숙소', 'Cuộc sống Tô Châu & Thượng Hải':'쑤저우 & 상하이 생활',
    'Tuyển sinh 2027':'2027 입학', 'Điều kiện dành cho học sinh Việt Nam':'베트남 학생 입학 조건',
    'Du học Trung Quốc':'중국 유학', 'Hướng dẫn du học Trung Quốc 2027':'2027 중국 유학 가이드',
    'Học đại học bằng tiếng Anh tại XJTLU':'XJTLU에서 영어로 대학 공부하기',
    'Tin tức XJTLU':'XJTLU 뉴스', 'Tin tức':'뉴스', 'Xem tin →':'뉴스 보기 →',
    'Tin chính thức đáng chú ý được chọn lọc và tóm tắt bằng tiếng Việt →':'주요 공식 뉴스를 선별해 한국어로 확인 →',
    'Tin XJTLU dành cho sinh viên Việt Nam':'베트남 학생을 위한 XJTLU 뉴스',
    'Tư vấn điện thoại TP.HCM':'호치민 전화상담', 'Tư vấn điện thoại Hà Nội':'하노이 전화상담',
    'Tư vấn Zalo':'Zalo 상담', 'SOS TP.HCM':'SOS 호치민', 'SOS Hà Nội':'SOS 하노이',
    'Cập nhật: 09/09/2026':'업데이트: 2026년 9월 9일', 'Trả lời nhanh:':'빠른 답변:',
    'Câu hỏi thường gặp':'자주 묻는 질문', 'Xem tiếp':'함께 보면 좋은 가이드',
}

COST = {
    'Chi phí sinh hoạt XJTLU 2027: mỗi tháng cần bao nhiêu?':'XJTLU 생활비 2027: 한 달에 얼마가 필요할까?',
    'Ba kịch bản ngân sách giúp sinh viên Việt Nam ước tính thực tế trước khi chọn chỗ ở và chuẩn bị tài chính.':'베트남 학생이 숙소를 선택하고 유학 예산을 준비하기 전에 참고할 수 있도록 월 생활비를 세 가지 수준으로 정리했습니다.',
    'mức tiết kiệm / tháng':'절약형 / 월', 'mức phổ biến / tháng':'일반형 / 월', 'mức thoải mái / tháng':'여유형 / 월',
    'Ba kịch bản ngân sách tham khảo hiện tại là khoảng':'현재 참고할 수 있는 월 생활비 예산은 약',
    '3.700 / 6.450 / 9.600 RMB mỗi tháng':'월 3,700 / 6,450 / 9,600 RMB',
    '. Chênh lệch lớn nhất thường đến từ loại chỗ ở, ăn uống và mức chi tiêu cá nhân.':' 정도이며, 가장 큰 차이는 주로 숙소 유형, 식비, 개인 소비 수준에서 발생합니다.',
    '3 mức ngân sách hàng tháng':'월 생활비 예산 3가지', 'Mức sống':'항목', 'Tiết kiệm':'절약형', 'Phổ biến':'일반형', 'Thoải mái / expat':'여유형',
    'Nhà ở':'숙소', 'Điện nước':'공과금', 'Điện thoại':'휴대전화', 'Ăn uống':'식비', 'Đi lại':'교통',
    'Giải trí / chi tiêu thêm':'여가 / 추가 지출', 'Tổng / tháng':'월 합계',
    'Đây là mẫu ngân sách để lập kế hoạch, không phải mức bắt buộc. Tỷ giá RMB/VND thay đổi nên nên quy đổi sang VND tại thời điểm chuẩn bị hồ sơ và thanh toán.':'위 금액은 예산 계획을 위한 참고 예시이며 필수 지출액은 아닙니다. RMB/VND 환율은 변동하므로 실제 서류 준비나 결제 시점에 가까운 환율로 환산하는 것이 좋습니다.',
    'Chi phí dễ bị quên':'놓치기 쉬운 추가 비용', 'Tiền đặt cọc nhà':'숙소 보증금',
    'Tùy nơi ở và hợp đồng; một số lựa chọn cần đặt cọc lớn hơn nếu trả tiền theo đợt.':'숙소와 계약 방식에 따라 다르며, 분할 납부 조건에 따라 보증금이 더 커질 수 있습니다.',
    'Phí dịch vụ học tập':'학업 관련 서비스 비용',
    'Nên dự trù khoảng 2.000 RMB/năm hoặc 1.000 RMB/học kỳ cho các khoản như giáo trình, thẻ, in ấn và dịch vụ liên quan.':'교재, 카드, 인쇄 및 관련 서비스 비용으로 연 약 2,000 RMB 또는 학기당 약 1,000 RMB 정도를 별도로 잡아두는 것이 좋습니다.',
    'Visa / giấy tờ':'비자 / 행정서류',
    'Có thể dự trù khoảng 400 RMB cho phí visa theo mức tham khảo hiện tại; các khoản thực tế cần kiểm tra tại thời điểm làm thủ tục.':'현재 참고 기준으로 비자 관련 비용 약 400 RMB를 예상할 수 있으나, 실제 비용은 수속 시점에 다시 확인해야 합니다.',
    'Vé máy bay & du lịch':'항공권 & 여행',
    'Vé về Việt Nam, đi Thượng Hải, tàu cao tốc và du lịch trong Trung Quốc có thể làm ngân sách tăng đáng kể.':'베트남 왕복 항공권, 상하이 이동, 고속철도, 중국 내 여행비는 전체 생활비를 크게 늘릴 수 있습니다.',
    'Tiết kiệm nhất ở đâu?':'생활비를 줄이려면?', 'Ăn trong campus':'캠퍼스 안에서 식사하기',
    'Canteen và đồ ăn địa phương thường giúp giảm đáng kể chi phí so với ăn nhà hàng quốc tế thường xuyên.':'교내 식당과 현지 음식을 이용하면 국제식 레스토랑을 자주 이용하는 것보다 식비를 크게 줄일 수 있습니다.',
    'Ưu tiên metro / bus':'지하철·버스 우선 이용',
    'SIP có hệ thống metro và bus thuận tiện. Taxi/DiDi dùng thường xuyên sẽ làm ngân sách tăng nhanh.':'SIP는 지하철과 버스 이용이 편리합니다. 택시나 DiDi를 자주 이용하면 교통비가 빠르게 늘어납니다.',
    'Chọn chỗ ở đúng nhu cầu':'필요에 맞는 숙소 선택',
    'Chỉ riêng tiền thuê có thể dao động từ khoảng 1.800 RMB/tháng trong kịch bản tiết kiệm đến trên 3.500 RMB cho studio tư nhân.':'숙소비만 해도 절약형 기준 월 약 1,800 RMB에서 개인 스튜디오의 경우 월 3,500 RMB 이상까지 차이가 날 수 있습니다.',
    'Không hard-code VND quá sớm':'VND 환산액을 너무 일찍 고정하지 않기',
    'Học phí và tiền nhà thanh toán bằng RMB; khi lập kế hoạch dài hạn nên giữ ngân sách gốc bằng RMB rồi quy đổi VND theo tỷ giá gần thời điểm thanh toán.':'학비와 숙소비는 RMB로 결제하므로 장기 예산은 RMB 기준으로 잡고, 실제 결제 시점에 가까운 환율로 VND로 환산하는 편이 안전합니다.',
    'Ngân sách 1 năm nên tính như thế nào?':'1년 예산은 어떻게 계산할까?',
    'Cách an toàn là tách riêng':'가장 안전한 방법은',
    'học phí + chỗ ở + sinh hoạt hàng tháng + bảo hiểm/visa + vé máy bay + quỹ dự phòng':'학비 + 숙소비 + 월 생활비 + 보험/비자 + 항공권 + 비상예산',
    '. Đừng lấy một con số “chi phí sinh hoạt Trung Quốc” chung cho mọi thành phố hoặc mọi kiểu sống.':'을 각각 따로 계산하는 것입니다. 중국 전체의 평균 생활비 하나를 모든 도시와 생활방식에 그대로 적용하지 않는 것이 좋습니다.',
    'Sinh viên XJTLU cần bao nhiêu tiền sinh hoạt mỗi tháng?':'XJTLU 학생은 한 달 생활비로 얼마가 필요할까요?',
    'Ba mức tham khảo hiện tại là khoảng 3.700 RMB cho lối sống tiết kiệm, 6.450 RMB cho mức phổ biến và 9.600 RMB cho lối sống thoải mái hơn.':'현재 참고 예산은 절약형 약 3,700 RMB, 일반형 약 6,450 RMB, 보다 여유로운 생활 기준 약 9,600 RMB입니다.',
    'Có nên đổi toàn bộ ngân sách sang VND ngay từ đầu không?':'처음부터 전체 예산을 VND로 환산해 두는 것이 좋을까요?',
    'Không nên cố định tỷ giá quá sớm. Các khoản chính được tính bằng RMB, vì vậy nên giữ ngân sách gốc bằng RMB và quy đổi VND gần thời điểm thanh toán.':'환율을 너무 일찍 고정하는 것은 권하지 않습니다. 주요 비용이 RMB 기준이므로 원예산은 RMB로 유지하고 실제 결제 시점에 가까워졌을 때 VND로 환산하는 편이 좋습니다.',
    'Học phí đã bao gồm ký túc xá và sinh hoạt chưa?':'학비에 숙소비와 생활비가 포함되어 있나요?',
    'Không. Học phí, chỗ ở, sinh hoạt, bảo hiểm, visa, đi lại và chi tiêu cá nhân cần được tính riêng.':'아닙니다. 학비, 숙소비, 생활비, 보험, 비자, 교통비, 개인지출은 각각 따로 계산해야 합니다.',
    'Ghép học phí với ngân sách sinh hoạt':'학비와 생활비를 함께 계산하기', 'So sánh loại phòng và giá':'객실 유형과 비용 비교',
    'Tô Châu & Thượng Hải':'쑤저우 & 상하이', 'Hiểu môi trường sống ngoài campus':'캠퍼스 밖 생활환경 확인',
}

DORM = {
    'Ký túc xá XJTLU: SIP và Taicang khác nhau thế nào?':'XJTLU 숙소: SIP와 타이창은 어떻게 다를까?',
    'So sánh các lựa chọn ở gần campus để chọn theo ngân sách, khoảng cách, phòng tắm, bếp và mức riêng tư.':'캠퍼스 인근 숙소의 비용, 거리, 욕실·주방 형태와 개인공간 수준을 비교해 선택할 수 있도록 정리했습니다.',
    'nhiều lựa chọn SIP đi bộ đến campus':'SIP 주요 숙소의 캠퍼스 도보거리',
    'twin room Taicang / giường / năm học':'타이창 트윈룸 / 침대당 / 학년',
    'single room Taicang / phòng / năm học':'타이창 싱글룸 / 객실당 / 학년',
    'Sinh viên quốc tế học tại SIP có nhiều lựa chọn quanh Dushu Lake; Taicang có XJTLU Entrepreneur Apartment ngay cạnh campus. Giá, loại phòng, hợp đồng và cách thanh toán khác nhau đáng kể.':'SIP에서 공부하는 국제학생은 Dushu Lake 주변의 여러 숙소를 선택할 수 있고, 타이창에는 캠퍼스 바로 옆 XJTLU Entrepreneur Apartment가 있습니다. 숙소별 가격, 객실 형태, 계약기간과 결제방식이 상당히 다릅니다.',
    'SIP: các lựa chọn phổ biến':'SIP: 주요 숙소 선택지', 'Khu ở':'숙소', 'Khoảng cách':'거리', 'Loại phòng / điểm chính':'객실 형태 / 주요 특징', 'Giá tham khảo':'참고 가격',
    '10–15 phút đi bộ':'도보 10–15분', 'Phòng ngủ riêng, phòng tắm riêng; bếp và không gian chung':'개인 침실·개인 욕실, 주방과 공용공간 공유',
    '57 RMB/ngày · hợp đồng 1 năm học':'57 RMB/일 · 1학년 계약', 'Studio A/B hoặc double room':'Studio A/B 또는 더블룸', '80–90 RMB/ngày':'80–90 RMB/일',
    'Khoảng 5 phút đi bộ':'도보 약 5분', 'Căn 3 phòng ngủ, phòng tắm chung, không có bếp':'3베드룸 아파트, 공용 욕실, 주방 없음', '50–54 RMB/ngày':'50–54 RMB/일',
    'Khoảng 10 phút đi bộ':'도보 약 10분', 'Studio hoặc one-bedroom, có bếp và phòng tắm riêng':'스튜디오 또는 1베드룸, 개인 주방·욕실', '85–102 RMB/ngày':'85–102 RMB/일',
    'Single / double, phòng tắm riêng, khu bếp & giặt chung':'싱글/더블룸, 개인 욕실, 공용 주방·세탁공간', '57–62 RMB/ngày':'57–62 RMB/일',
    'Taicang: ở ngay cạnh XEC':'타이창: XEC 바로 옆 숙소',
    'XJTLU Entrepreneur Apartment nằm cách lớp học khoảng 5–10 phút đi bộ. Phòng có giường, tủ, bàn học, phòng tắm và ban công nhỏ.':'XJTLU Entrepreneur Apartment는 강의동에서 도보 약 5–10분 거리에 있습니다. 객실에는 침대, 옷장, 책상, 욕실, 작은 발코니가 마련되어 있습니다.',
    'Twin room':'트윈룸', '6.000 RMB/giường/năm học':'6,000 RMB/침대/학년', '. Ngoài ra có cách tính theo tháng hoặc theo ngày trong một số trường hợp.':'이며, 경우에 따라 월 단위 또는 일 단위 요금이 적용될 수도 있습니다.',
    'Single room':'싱글룸', '14.000 RMB/phòng/năm học':'14,000 RMB/객실/학년', '. Phù hợp nếu ưu tiên không gian riêng.':'이며, 개인공간을 우선하는 학생에게 적합합니다.',
    'Không được nấu ăn trong phòng ở Taicang và có hạn chế với một số thiết bị điện. Hãy đọc kỹ nội quy trước khi chọn.':'타이창 숙소 객실 내 취사는 금지되어 있으며 일부 전기제품 사용에도 제한이 있습니다. 선택 전에 숙소 규정을 확인하세요.',
    'Lưu ý đặc biệt cho sinh viên Taicang Year 1':'타이창 전공 Year 1 학생이 꼭 알아둘 점', 'Quan trọng:':'중요:',
    'sinh viên đại học năm 1 được nhận vào các chương trình XEC Taicang bắt đầu học tại':'XEC 타이창 프로그램에 입학한 학부 1학년 학생은',
    '. Vì vậy năm đầu cần đặt chỗ ở SIP, không phải Taicang.':'에서 첫해를 시작합니다. 따라서 1학년에는 타이창이 아니라 SIP 숙소를 예약해야 합니다.',
    'Đặt phòng và tiền đặt cọc':'예약과 보증금', 'Chỗ ở do đơn vị bên ngoài quản lý, XJTLU hỗ trợ đặt phòng sau khi sinh viên hoàn tất bước xác nhận nhập học. Một số hợp đồng yêu cầu 1 năm học; Wenhua có thể cho 1 học kỳ hoặc 1 năm.':'SIP 주요 숙소는 외부 업체가 운영하며, XJTLU는 학생이 입학확인 절차를 마친 뒤 예약 과정을 지원합니다. 일부 숙소는 1학년 단위 계약이 필요하고 Wenhua는 한 학기 또는 1년 계약이 가능합니다.',
    'Phòng phụ thuộc tình trạng còn chỗ và nguyên tắc first come, first served. Sinh viên XEC cần thanh toán toàn bộ tiền thuê bằng chuyển khoản trước khi đến Trung Quốc; nên chừa 2–3 tuần để xử lý.':'객실은 잔여 수량에 따라 선착순으로 배정됩니다. XEC 학생은 중국 입국 전에 계좌이체로 숙소비 전액을 납부해야 하므로 처리기간으로 2–3주 정도 여유를 두는 것이 좋습니다.',
    'Chọn loại phòng theo ưu tiên':'우선순위에 따른 숙소 선택', 'Muốn gần campus nhất':'캠퍼스와 가까운 곳을 원한다면',
    'MBA ở SIP khoảng 5 phút đi bộ; Taicang Entrepreneur Apartment khoảng 5–10 phút.':'SIP의 MBA Apartments는 도보 약 5분, Taicang Entrepreneur Apartment는 약 5–10분 거리입니다.',
    'Muốn bếp riêng':'주방을 원한다면', "Scholar's Apartments có lựa chọn studio / one-bedroom với bếp; Parfait International có bếp dùng chung trong căn hộ.":"Scholar's Apartments는 주방이 있는 스튜디오/1베드룸을 선택할 수 있고, Parfait International은 아파트 내 공용 주방을 이용합니다.",
    'Muốn phòng tắm riêng':'개인 욕실을 원한다면', 'Parfait International, Wenhua và nhiều loại studio cung cấp phòng tắm riêng. MBA dùng phòng tắm chung.':'Parfait International, Wenhua 및 여러 스튜디오형 숙소는 개인 욕실을 제공하며 MBA Apartments는 욕실을 공유합니다.',
    'Muốn chi phí thấp hơn':'비용을 낮추고 싶다면', 'So sánh giá theo ngày/năm, tiền đặt cọc, điện nước và độ dài hợp đồng. Đừng chỉ nhìn giá thuê niêm yết.':'일·연 단위 요금뿐 아니라 보증금, 공과금, 계약기간까지 함께 비교하세요. 표시된 임대료만 보고 결정하지 않는 것이 좋습니다.',
    'Sinh viên XJTLU ở SIP có ký túc xá trong campus không?':'XJTLU SIP 학생이 캠퍼스 안 기숙사에 거주하나요?',
    'Các lựa chọn quốc tế chính nằm trong khu Dushu Lake gần campus và được đơn vị bên ngoài quản lý; XJTLU hỗ trợ sinh viên trong quá trình đặt chỗ.':'국제학생이 주로 이용하는 숙소는 캠퍼스 인근 Dushu Lake 지역에 있으며 외부 업체가 운영합니다. XJTLU는 예약 과정에서 학생을 지원합니다.',
    'Sinh viên chương trình Taicang có ở Taicang ngay từ năm 1 không?':'타이창 프로그램 학생은 1학년부터 타이창에서 생활하나요?',
    'Không. Sinh viên đại học Year 1 của các chương trình XEC Taicang bắt đầu tại SIP và nên đặt chỗ ở SIP cho năm đầu.':'아닙니다. XEC 타이창 프로그램의 학부 Year 1 학생은 SIP에서 첫해를 시작하므로 1학년에는 SIP 숙소를 예약해야 합니다.',
    'Taicang có phòng đơn không?':'타이창에 싱글룸이 있나요?', 'Có. XJTLU Entrepreneur Apartment có twin room và single room; giá năm học hiện được niêm yết lần lượt 6.000 RMB/giường và 14.000 RMB/phòng.':'네. XJTLU Entrepreneur Apartment에는 트윈룸과 싱글룸이 있으며, 현재 학년 기준 요금은 각각 6,000 RMB/침대와 14,000 RMB/객실입니다.',
    'Chi phí sinh hoạt 2027':'2027 생활비', 'Ghép tiền nhà với ngân sách tháng':'숙소비와 월 생활비 함께 계산', 'Thể thao, CLB và video campus':'스포츠, 동아리와 캠퍼스 영상', 'Xem môi trường sống quanh campus':'캠퍼스 주변 생활환경 확인',
}

CITY = {
    'Tô Châu, Thượng Hải và Việt Nam: vì sao vị trí XJTLU đáng chú ý?':'쑤저우·상하이와 베트남: XJTLU의 위치가 주목할 만한 이유',
    'Học bằng tiếng Anh tại Trung Quốc, nhưng sống trong một vùng kinh tế có liên kết trực tiếp với Việt Nam.':'중국에서 영어로 공부하면서 베트남과 직접 연결된 경제권을 경험할 수 있습니다.',
    'thương mại Tô Châu – Việt Nam 2025':'2025 쑤저우–베트남 교역', 'tàu cao tốc Shanghai Hongqiao – Tô Châu':'Shanghai Hongqiao–쑤저우 고속철도', 'học giữa trung tâm công nghệ – sản xuất quốc tế':'국제 기술·제조 중심지에서 공부',
    'Tô Châu không chỉ là “thành phố gần Thượng Hải”. Với sinh viên Việt Nam, đây là một trung tâm sản xuất – thương mại có quan hệ trực tiếp và rất lớn với Việt Nam, đồng thời nằm trong vùng kinh tế Trường Giang cùng Thượng Hải.':'쑤저우는 단순히 ‘상하이 근처 도시’가 아닙니다. 베트남 학생의 관점에서 보면 베트남과 직접적인 대규모 교역관계를 가진 제조·무역 중심지이며, 상하이와 함께 장강삼각주 경제권에 속합니다.',
    'Việt Nam là đối tác thương mại lớn của Tô Châu':'베트남은 쑤저우의 주요 교역 파트너', 'Năm 2025, kim ngạch xuất nhập khẩu giữa Tô Châu và Việt Nam đạt khoảng':'2025년 쑤저우와 베트남의 수출입 규모는 약',
    ', tăng 29,1%. Đến 2026, Việt Nam là đối tác thương mại lớn thứ hai của Tô Châu và là đối tác lớn nhất của thành phố trong ASEAN.':'로 전년 대비 29.1% 증가했습니다. 2026년 기준 베트남은 쑤저우의 두 번째로 큰 교역 파트너이며 ASEAN 국가 가운데서는 가장 큰 교역 파트너입니다.',
    'thương mại Tô Châu – Việt Nam năm 2025':'2025년 쑤저우–베트남 교역', 'tăng trưởng so với năm trước':'전년 대비 증가율', 'tăng trưởng 4 tháng đầu 2026':'2026년 1–4월 증가율',
    'Điểm đáng chú ý là mối liên kết này đến từ các ngành rất gần với chương trình của XJTLU: điện tử, thiết bị máy móc, dệt may, sản xuất, logistics và chuỗi cung ứng.':'이 교역관계가 전자, 기계·장비, 섬유, 제조, 물류, 공급망 등 XJTLU 전공과 연결하기 쉬운 산업에서 형성된다는 점도 주목할 만합니다.',
    'Từ Tô Châu đến Việt Nam: đường sắt, đường bộ, hàng không và đường biển':'쑤저우에서 베트남까지: 철도·도로·항공·해운 연결', 'Hành lang logistics mới':'새로운 물류 통로',
    'Tháng 6/2026, Tô Châu đồng thời khai trương tuyến tàu hàng quốc tế, xe tải quốc tế và chuyến bay hàng hóa charter đi Việt Nam. Thành phố đã có sẵn các tuyến đường biển Đông Nam Á.':'2026년 6월 쑤저우는 베트남을 연결하는 국제 화물열차, 국제 트럭 노선, 화물 전세기를 동시에 개통했습니다. 동남아시아 방향 해상노선도 이미 운영되고 있습니다.',
    'Ý nghĩa với sinh viên':'학생에게 어떤 의미가 있을까?', 'Học supply chain, business, economics, engineering, data hay công nghệ tại đây đồng nghĩa bạn đang sống trong một khu vực có luồng thương mại thật với Việt Nam, thay vì chỉ học khái niệm trong lớp.':'Supply Chain, Business, Economics, Engineering, Data, Technology 등을 공부한다면 교실 안 이론뿐 아니라 실제 베트남과 상품·산업이 오가는 지역에서 생활하며 공부하게 됩니다.',
    'Thượng Hải mở rộng “bán kính” của XJTLU':'상하이가 넓혀주는 XJTLU의 생활·경험 반경', 'Tô Châu và Thượng Hải nằm rất gần nhau. Từ Shanghai Hongqiao đến Tô Châu có nhiều chuyến tàu cao tốc khoảng 25–30 phút; từ sân bay Hongqiao đến XJTLU SIP khoảng 70 km, còn từ Pudong khoảng 120 km.':'쑤저우와 상하이는 매우 가깝습니다. Shanghai Hongqiao에서 쑤저우까지 고속철도로 약 25–30분 걸리는 편이 많고, Hongqiao 공항에서 XJTLU SIP는 약 70km, Pudong 공항에서는 약 120km 거리입니다.',
    'Hà Nội / TP.HCM → Thượng Hải':'하노이 / 호치민 → 상하이', 'Vietnam Airlines hiện bán hành trình Hà Nội – Thượng Hải và TP.HCM – Thượng Hải. Vì vậy với sinh viên Việt Nam, Thượng Hải là cửa ngõ hàng không thực tế để đến XJTLU.':'Vietnam Airlines는 현재 하노이–상하이와 호치민–상하이 노선을 판매하고 있습니다. 베트남 학생에게 상하이는 XJTLU로 이동할 때 현실적인 항공 관문입니다.',
    'Thượng Hải – TP.HCM':'상하이–호치민', 'Hai thành phố tiếp tục mở rộng hợp tác về đầu tư, thương mại, tài chính, chuyển đổi số, phát triển xanh, giáo dục và giao lưu thanh niên. Với sinh viên Việt Nam, “Tô Châu + Thượng Hải” tạo thành một vùng học tập và trải nghiệm rộng hơn một thành phố.':'두 도시는 투자, 무역, 금융, 디지털 전환, 친환경 성장, 교육, 청년교류 등 다양한 분야에서 협력을 확대하고 있습니다. 베트남 학생에게 ‘쑤저우 + 상하이’는 한 도시를 넘어서는 더 넓은 학업·생활 경험권을 만듭니다.',
    'Ngành nào ở XJTLU hưởng lợi nhiều nhất từ bối cảnh này?':'이 환경과 특히 잘 맞는 XJTLU 전공은?',
    'Quan sát trực tiếp chuỗi cung ứng Trung Quốc – Việt Nam, logistics, thương mại và doanh nghiệp đa quốc gia.':'중국–베트남 공급망, 물류, 무역, 다국적 기업 활동을 가까이에서 이해할 수 있습니다.',
    'SIP là khu vực tập trung công nghệ và doanh nghiệp quốc tế; dữ liệu và tự động hóa gắn chặt với sản xuất – logistics.':'SIP에는 기술기업과 국제기업이 밀집해 있으며 데이터와 자동화는 제조·물류와 밀접하게 연결됩니다.',
    'Tô Châu mạnh về điện tử, thiết bị và sản xuất; đây cũng là nhóm ngành có liên kết thương mại lớn với Việt Nam.':'쑤저우는 전자, 장비, 제조산업이 강하고 이들 분야는 베트남과의 교역 비중도 큰 편입니다.',
    'Thương mại xuyên biên giới và vị trí gần Thượng Hải giúp sinh viên thấy rõ hơn cách dòng vốn, sản xuất và thị trường vận hành trong khu vực.':'국경 간 무역과 상하이 인접성 덕분에 자본, 생산, 시장이 지역 안에서 어떻게 움직이는지 이해하기 좋은 환경입니다.',
    'Bối cảnh thành phố không đảm bảo việc làm hay thực tập. Giá trị nằm ở việc học bằng tiếng Anh trong khi sống giữa một hệ sinh thái kinh tế có liên hệ trực tiếp với Việt Nam.':'도시의 산업환경이 취업이나 인턴십을 보장하는 것은 아닙니다. 의미는 영어로 학위과정을 공부하면서 베트남과 직접 연결된 경제 생태계 안에서 생활한다는 데 있습니다.',
    'Cuộc sống: một thành phố Trung Quốc, nhưng không bị tách khỏi châu Á':'생활환경: 중국 도시이면서 아시아와 연결된 쑤저우', 'Tô Châu có khu phố cổ, kênh đào và vườn truyền thống, đồng thời SIP lại là khu đô thị hiện đại với trung tâm thương mại, tàu điện ngầm, hồ Jinji và nhiều doanh nghiệp quốc tế. Khi cần nhiều lựa chọn hơn về sự kiện, mua sắm, hàng không hay trải nghiệm quốc tế, Thượng Hải ở ngay bên cạnh.':'쑤저우에는 구시가지, 운하, 전통 정원이 있고 SIP에는 쇼핑몰, 지하철, 진지호(Jinji Lake), 국제기업이 모인 현대적인 도시환경이 있습니다. 더 다양한 행사, 쇼핑, 항공편, 국제적인 경험이 필요하면 상하이도 가까이 이용할 수 있습니다.',
    'Tô Châu có gần Thượng Hải không?':'쑤저우는 상하이와 가까운가요?', 'Có. Tàu cao tốc từ Shanghai Hongqiao đến Tô Châu thường mất khoảng 25–30 phút; XJTLU SIP cách sân bay Hongqiao khoảng 70 km.':'네. Shanghai Hongqiao에서 쑤저우까지 고속철도는 보통 약 25–30분이며, XJTLU SIP는 Hongqiao 공항에서 약 70km 거리입니다.',
    'Tô Châu có quan hệ kinh tế đáng kể với Việt Nam không?':'쑤저우와 베트남의 경제관계가 실제로 큰가요?', 'Có. Năm 2025 thương mại Tô Châu – Việt Nam đạt khoảng 204,75 tỷ RMB; Việt Nam hiện là đối tác thương mại lớn thứ hai của Tô Châu và lớn nhất trong ASEAN.':'네. 2025년 쑤저우–베트남 교역규모는 약 204.75 billion RMB였으며, 현재 베트남은 쑤저우의 두 번째로 큰 교역 파트너이자 ASEAN 내 최대 교역 파트너입니다.',
    'Học ở Tô Châu có nghĩa phải làm việc tại Trung Quốc sau tốt nghiệp không?':'쑤저우에서 공부하면 졸업 후 반드시 중국에서 취업해야 하나요?', 'Không. Điểm mạnh là có thêm trải nghiệm Trung Quốc và hiểu thị trường trong khi học bằng tiếng Anh; kế hoạch nghề nghiệp có thể ở Việt Nam, Trung Quốc hoặc thị trường khác.':'아닙니다. 영어로 공부하면서 중국 경험과 시장 이해를 더할 수 있다는 점이 강점이며, 졸업 후 진로는 베트남·중국·다른 국가 중에서 선택할 수 있습니다.',
    'Xem ngành phù hợp với mục tiêu Việt Nam – Trung Quốc':'베트남–중국 진로 목표에 맞는 전공 보기', 'Chi phí sinh hoạt':'생활비', 'Lập ngân sách thực tế tại Tô Châu':'쑤저우 실제 생활비 예산 확인', 'Ký túc xá':'숙소', 'So sánh SIP và Taicang':'SIP와 타이창 비교',
}

TITLE_META = {
    'xjtlu-chi-phi-sinh-hoat-2027.html':('[한글 검수판] XJTLU 생활비 2027 | 쑤저우 월 예산 3가지','XJTLU 쑤저우 생활비를 월 3,700·6,450·9,600 RMB의 세 가지 예산 수준으로 나누어 숙소, 식비, 공과금, 교통비와 개인지출까지 정리합니다.'),
    'xjtlu-ky-tuc-xa-sip-taicang.html':('[한글 검수판] XJTLU 숙소 2027 | SIP & 타이창 객실·비용·거리','XJTLU SIP와 타이창 숙소의 객실 유형, 비용, 캠퍼스 거리, 주방·욕실, 보증금과 국제학생이 확인할 사항을 비교합니다.'),
    'xjtlu-to-chau-thuong-hai-viet-nam.html':('[한글 검수판] 쑤저우·상하이 & 베트남 | XJTLU','쑤저우와 베트남의 교역관계, 상하이 접근성, 물류·산업환경과 이러한 위치가 XJTLU 베트남 학생에게 갖는 의미를 정리합니다.'),
}
PAGE_MAP={'xjtlu-chi-phi-sinh-hoat-2027.html':COST,'xjtlu-ky-tuc-xa-sip-taicang.html':DORM,'xjtlu-to-chau-thuong-hai-viet-nam.html':CITY}


def translate_new_page(rel: str):
    src=SOURCE/rel
    if not src.exists(): raise SystemExit(f'missing source {src}')
    shutil.copy2(src, ROOT/rel)
    p=ROOT/rel
    soup=BeautifulSoup(p.read_text(encoding='utf-8'),'html.parser')
    if soup.html: soup.html['lang']='ko'
    for t in soup.find_all('meta',attrs={'name':re.compile('^robots$',re.I)}): t.decompose()
    robots=soup.new_tag('meta'); robots['name']='robots'; robots['content']='noindex, nofollow, noarchive, nosnippet'
    if soup.head: soup.head.insert(0,robots)
    for t in soup.find_all('link',attrs={'rel':lambda x:x and 'canonical' in x}): t.decompose()
    for t in soup.find_all('meta',attrs={'property':'og:url'}): t.decompose()
    for t in soup.find_all('script',attrs={'type':'application/ld+json'}): t.decompose()
    loc=soup.find('meta',attrs={'property':'og:locale'})
    if loc: loc['content']='ko_KR'
    mapping={**COMMON,**PAGE_MAP[rel]}
    for node in list(soup.find_all(string=True)):
        if isinstance(node,Comment) or not node.parent or node.parent.name in {'script','style','svg','path','noscript','code','pre'}: continue
        raw=str(node); key=' '.join(raw.split())
        if key in mapping:
            lead=raw[:len(raw)-len(raw.lstrip())]; trail=raw[len(raw.rstrip()):]
            node.replace_with(NavigableString(lead+mapping[key]+trail))
    title,desc=TITLE_META[rel]
    if soup.title: soup.title.string=title
    d=soup.find('meta',attrs={'name':'description'})
    if d: d['content']=desc
    for prop in ('og:title','og:description','og:site_name'):
        tag=soup.find('meta',attrs={'property':prop})
        if not tag: continue
        if prop=='og:title': tag['content']=title.replace('[한글 검수판] ','')
        elif prop=='og:description': tag['content']=desc
        else: tag['content']='XJTLU 베트남'
    for tag in soup.find_all(True):
        for attr in ('aria-label','title','alt','placeholder'):
            v=tag.get(attr)
            if isinstance(v,str) and v in mapping: tag[attr]=mapping[v]
        href=tag.get('href')
        if isinstance(href,str) and href.startswith(PROD_HOST): tag['href']=REVIEW_HOST+href[len(PROD_HOST):]
    # Review badge, exactly once.
    for old in soup.select('#tns-korean-review-banner-style,.tns-korean-review-banner'): old.decompose()
    css=soup.new_tag('style'); css['id']='tns-korean-review-banner-style'; css.string=".tns-korean-review-banner{position:fixed;left:10px;bottom:10px;z-index:9999;background:rgba(11,22,48,.92);color:#fff;padding:7px 10px;border-radius:7px;font:700 11px/1.2 system-ui,-apple-system,'Segoe UI',sans-serif;box-shadow:0 4px 16px rgba(0,0,0,.18)}"
    if soup.head: soup.head.append(css)
    badge=soup.new_tag('div'); badge['class']='tns-korean-review-banner'; badge.string='한글 검수판 · 검색 비노출'
    if soup.body: soup.body.append(badge)
    rendered=str(soup).replace(PROD_HOST,REVIEW_HOST)
    if rendered.lstrip().startswith('<html'): rendered='<!DOCTYPE html>\n'+rendered
    p.write_text(rendered,encoding='utf-8')


def add_anchor_after(soup, after_href, new_href, label):
    if soup.find('a',href=new_href): return
    a=soup.find('a',href=after_href)
    if not a: return
    n=soup.new_tag('a',href=new_href); n.string=label
    a.insert_after(n)


def update_existing_menus():
    pages=sorted(ROOT.glob('*.html'))+sorted((ROOT/'news').glob('*.html'))
    for p in pages:
        if p.name in NEW_PAGES: continue
        soup=BeautifulSoup(p.read_text(encoding='utf-8'),'html.parser')
        if soup.select_one('.tns-site-menu-grid'):
            add_anchor_after(soup,'/university-of-liverpool-vietnam.html','/xjtlu-to-chau-thuong-hai-viet-nam.html','쑤저우·상하이 & 베트남')
            add_anchor_after(soup,'/xjtlu-hoc-phi-hoc-bong-2027.html','/xjtlu-chi-phi-sinh-hoat-2027.html','XJTLU 생활비 2027')
            if not soup.find('a',href='/xjtlu-ky-tuc-xa-sip-taicang.html'):
                a=soup.find('a',href='/xjtlu-doi-song-sinh-vien-the-thao-cau-lac-bo.html#video')
                if a:
                    city=soup.new_tag('a',href='/xjtlu-to-chau-thuong-hai-viet-nam.html'); city.string='쑤저우 & 상하이'
                    dorm=soup.new_tag('a',href='/xjtlu-ky-tuc-xa-sip-taicang.html'); dorm.string='SIP & 타이창 숙소'
                    a.insert_after(city); a.insert_after(dorm)
        p.write_text(str(soup),encoding='utf-8')


def update_homepage():
    p=ROOT/'index.html'; soup=BeautifulSoup(p.read_text(encoding='utf-8'),'html.parser')
    if not soup.find('a',href='/xjtlu-chi-phi-sinh-hoat-2027.html'):
        anchor=soup.find('a',href='/xjtlu-doi-song-sinh-vien-the-thao-cau-lac-bo.html')
        container=anchor.parent if anchor else None
        if container:
            row=soup.new_tag('div'); row['style']='display:flex;flex-wrap:wrap;gap:8px 16px;margin-top:12px;font-size:12.5px;font-weight:700;color:#596273'
            for href,label in [('/xjtlu-to-chau-thuong-hai-viet-nam.html','쑤저우 & 베트남 →'),('/xjtlu-chi-phi-sinh-hoat-2027.html','2027 생활비 →'),('/xjtlu-ky-tuc-xa-sip-taicang.html','SIP & 타이창 숙소 →')]:
                a=soup.new_tag('a',href=href); a.string=label; row.append(a)
            container.insert_after(row)
    p.write_text(str(soup),encoding='utf-8')


def update_major():
    p=ROOT/'xjtlu-nganh-hoc-nghe-nghiep.html'; soup=BeautifulSoup(p.read_text(encoding='utf-8'),'html.parser')
    if soup.find(string=lambda x:isinstance(x,str) and '쑤저우–베트남 경제관계에서 주목할 전공은?' in x): return
    faq=soup.find('section',class_=lambda c:c and 'faq' in c.split())
    if not faq: return
    html='''<section class="section"><h2>쑤저우–베트남 경제관계에서 주목할 전공은?</h2><p class="lead">2025년 쑤저우–베트남 교역규모는 약 204.75 billion RMB였습니다. 쑤저우의 강점인 전자, 기계, 제조, 물류 산업은 베트남의 제조업과도 밀접하게 연결됩니다.</p><div class="grid"><article class="card"><h3>Supply Chain & Business</h3><p>중국–베트남 상품 흐름, 물류와 무역을 이해하고 싶은 학생에게 잘 맞는 환경입니다.</p></article><article class="card"><h3>AI, Data & Computer Science</h3><p>데이터, 자동화, 소프트웨어는 제조·물류·디지털 무역과 점점 더 밀접하게 연결되고 있습니다.</p></article><article class="card"><h3>Engineering & Manufacturing</h3><p>쑤저우는 대규모 산업 중심지로 공학과 스마트 제조를 공부하는 학생에게 실제 산업 맥락을 제공합니다.</p></article><article class="card"><h3>Economics & Finance</h3><p>상하이 인접성과 베트남과의 큰 교역규모는 지역 시장을 이해하는 데 좋은 배경이 됩니다.</p></article></div><div class="notice">이러한 환경이 취업을 보장한다는 뜻은 아닙니다. 베트남과 직접 연결된 경제 생태계 안에서 공부한다는 점에 의미가 있습니다.</div><p style="margin-top:13px"><a href="/xjtlu-to-chau-thuong-hai-viet-nam.html" style="font-weight:800;color:var(--navy)">쑤저우·상하이 & 베트남 자세히 보기 →</a></p></section>'''
    frag=BeautifulSoup(html,'html.parser').section; faq.insert_before(frag)
    p.write_text(str(soup),encoding='utf-8')


def update_student_life():
    p=ROOT/'xjtlu-doi-song-sinh-vien-the-thao-cau-lac-bo.html'; soup=BeautifulSoup(p.read_text(encoding='utf-8'),'html.parser')
    if soup.find(string=lambda x:isinstance(x,str) and '수업 밖 생활: 숙소, 예산, 쑤저우' in x): return
    target=None
    for sec in soup.find_all('section',class_=lambda c:c and 'section' in c.split()):
        h2=sec.find('h2')
        if h2 and h2.get_text(' ',strip=True) in {'함께 보면 좋은 가이드','계속 보기','Xem tiếp'}:
            target=sec; break
    if not target: return
    html='''<section class="section"><h2>수업 밖 생활: 숙소, 예산, 쑤저우</h2><p class="lead">스포츠와 동아리까지 확인했다면 다음으로 많이 궁금한 것은 어디에서 살지, 한 달에 얼마가 필요한지, 쑤저우가 베트남과 어떤 관계가 있는지입니다.</p><div class="related"><a href="/xjtlu-ky-tuc-xa-sip-taicang.html">SIP & 타이창 숙소<span>가격, 객실 유형, 거리, 주방·욕실 비교</span></a><a href="/xjtlu-chi-phi-sinh-hoat-2027.html">2027 생활비<span>월 3,700 / 6,450 / 9,600 RMB 예산 비교</span></a><a href="/xjtlu-to-chau-thuong-hai-viet-nam.html">쑤저우 & 상하이<span>베트남과의 연결, 교통과 경제환경</span></a></div></section>'''
    frag=BeautifulSoup(html,'html.parser').section; target.insert_before(frag)
    p.write_text(str(soup),encoding='utf-8')

for rel in NEW_PAGES: translate_new_page(rel)
update_existing_menus(); update_homepage(); update_major(); update_student_life()
print('Human Korean current-guide sync complete:',NEW_PAGES)
