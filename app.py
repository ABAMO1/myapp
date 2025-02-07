import streamlit as st
import requests
from datetime import datetime
import pandas as pd

# Configure Streamlit page
st.set_page_config(
    page_title="نظام تحليل الحالة الغذائية",
    page_icon="🥗",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'About': "### نظام تحليل الحالة الغذائية\nتطوير: م. إبراهيم الجحيشي"
    }
)

# تخصيص CSS
st.markdown("""
<style>
    .main {
        padding: 2rem;
    }
    .stButton > button {
        width: 100%;
        background-color: #4CAF50;
        color: white;
        padding: 0.5rem;
        border-radius: 10px;
    }
    .stButton > button:hover {
        background-color: #45a049;
    }
    .vitamin-card {
        background-color: #f8f9fa;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    h1 {
        color: #2c3e50;
        text-align: center;
        margin-bottom: 2rem;
    }
    h2 {
        color: #34495e;
        border-bottom: 2px solid #eee;
        padding-bottom: 0.5rem;
    }
    .metric-card {
        background-color: white;
        padding: 1rem;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
    }
    .report-section {
        background: white;
        padding: 2rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin: 1rem 0;
    }
    .report-header {
        color: #2c3e50;
        border-bottom: 2px solid #eee;
        padding-bottom: 0.5rem;
        margin-bottom: 1rem;
    }
    .report-item {
        padding: 0.8rem;
        margin: 0.5rem 0;
        background: #f8f9fa;
        border-left: 4px solid #4CAF50;
        border-radius: 4px;
    }
    .vitamin-status {
        display: inline-block;
        padding: 0.25rem 0.5rem;
        border-radius: 4px;
        margin-left: 0.5rem;
        font-weight: bold;
    }
    .status-normal { background-color: #d4edda; color: #155724; }
    .status-low { background-color: #f8d7da; color: #721c24; }
    .status-high { background-color: #fff3cd; color: #856404; }
    .results-container {
        background: linear-gradient(to bottom right, #ffffff, #f8f9fa);
        border-radius: 15px;
        padding: 2rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin: 2rem 0;
    }
    .section-header {
        background: linear-gradient(145deg, #4CAF50, #45a049);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 1.5rem;
        text-align: center;
    }
    .analysis-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        margin-bottom: 1rem;
        border-right: 4px solid;
    }
    .vitamin-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
        gap: 1rem;
        margin: 1rem 0;
    }
    .recommendation-list {
        list-style: none;
        padding: 0;
    }
    .recommendation-item {
        background: #f8f9fa;
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 8px;
        border-right: 4px solid #4CAF50;
        transition: transform 0.2s;
    }
    .recommendation-item:hover {
        transform: translateX(-5px);
    }
    .status-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 15px;
        font-weight: bold;
        margin-right: 0.5rem;
    }
    .normal { background-color: #d4edda; color: #155724; }
    .warning { background-color: #fff3cd; color: #856404; }
    .danger { background-color: #f8d7da; color: #721c24; }
    .metrics-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 1rem;
        margin: 1rem 0;
    }
    .metric-box {
        background: white;
        padding: 1rem;
        border-radius: 10px;
        text-align: center;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .metric-value {
        font-size: 1.5rem;
        font-weight: bold;
        color: #2c3e50;
        margin: 0.5rem 0;
    }
    .styled-table {
        width: 100%;
        border-collapse: collapse;
        margin: 1rem 0;
        font-size: 0.9em;
        border-radius: 8px;
        overflow: hidden;
        box-shadow: 0 0 20px rgba(0, 0, 0, 0.1);
    }
    .styled-table thead tr {
        background: linear-gradient(145deg, #4CAF50, #45a049);
        color: white;
        text-align: right;
        font-weight: bold;
    }
    .styled-table th,
    .styled-table td {
        padding: 12px 15px;
        text-align: right;
    }
    .styled-table tbody tr {
        border-bottom: 1px solid #dddddd;
        background-color: white;
    }
    .styled-table tbody tr:last-of-type {
        border-bottom: 2px solid #4CAF50;
    }
    .styled-table tbody tr:hover {
        background-color: #f5f5f5;
    }
    .status-cell {
        font-weight: bold;
        padding: 5px 10px;
        border-radius: 15px;
        display: inline-block;
    }
    .category-header {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        margin: 1.5rem 0 1rem 0;
        border-right: 4px solid #4CAF50;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# عنوان التطبيق مع أيقونة
st.markdown("<h1>🌿 نظام تحليل الحالة الغذائية والفيتامينات</h1>", unsafe_allow_html=True)

# إنشاء تخطيط ثنائي العمود
col1, col2 = st.columns([1, 1])

# تحديث قسم المعلومات الشخصية
with col1:
    st.markdown("### 👤 المعلومات الشخصية")
    with st.container():
        age = st.number_input("العمر", min_value=0, max_value=120, step=1)
        gender = st.selectbox("الجنس", ["ذكر", "أنثى"])
        weight = st.number_input("الوزن (كجم)", min_value=0.0, step=0.1)
        height = st.number_input("الطول (سم)", min_value=0.0, step=0.1)
        
        # إضافة معلومات الوجبات
        st.subheader("🍽️ معلومات الوجبات اليومية")
        meals_count = st.number_input("عدد الوجبات اليومية", min_value=1, max_value=6, value=3)
        breakfast = st.checkbox("فطور")
        lunch = st.checkbox("غداء")
        dinner = st.checkbox("عشاء")
        snacks = st.multiselect("الوجبات الخفيفة", ["صباحية", "مسائية", "ليلية"])

    st.markdown("### 🌞 نمط الحياة")
    with st.container():
        st.subheader("☀️ التعرض للشمس")
        sun_exposure = st.slider("عدد ساعات التعرض للشمس يومياً", 0.0, 12.0, 1.0)
        sun_context = st.selectbox("سياق التعرض للشمس", [
            "العمل في الخارج",
            "المشي اليومي",
            "الرياضة الخارجية",
            "محدود (داخل المباني معظم الوقت)"
        ])
        
        st.subheader("🏃 النشاط البدني")
        activity_level = st.select_slider(
            "مستوى النشاط البدني",
            options=["خامل", "خفيف", "معتدل", "نشط", "رياضي محترف"]
        )
        physical_activities = st.multiselect("أنواع النشاط البدني", [
            "مشي", "جري", "سباحة", "تمارين قوة", 
            "يوغا", "رياضات جماعية", "دراجات"
        ])
        exercise_duration = st.number_input("مدة التمارين اليومية (دقيقة)", min_value=0, max_value=300, step=15)

with col2:
    st.markdown("### 😴 نمط النوم والتوتر")
    with st.container():
        sleep_hours = st.slider("عدد ساعات النوم", 0, 12, 8)
        sleep_quality = st.select_slider(
            "جودة النوم",
            options=["سيئة جداً", "سيئة", "متوسطة", "جيدة", "ممتازة"]
        )
        stress_level = st.select_slider(
            "مستوى التوتر اليومي",
            options=["منخفض", "متوسط", "عالي"]
        )

    st.markdown("### 🥗 النظام الغذائي")
    with st.container():
        diet_type = st.selectbox("نوع النظام الغذائي", [
            "غير نباتي",
            "نباتي",
            "نباتي مع أسماك",
            "نباتي مع منتجات ألبان",
            "مختلط"
        ])
        
        st.subheader("📋 مكونات الوجبات الرئيسية")
        meal_components = st.multiselect("المكونات الرئيسية المعتادة", [
            "خضروات طازجة", "فواكه", "لحوم حمراء", "دواجن", 
            "أسماك", "بقوليات", "حبوب كاملة", "منتجات ألبان",
            "مكسرات وبذور", "زيوت نباتية"
        ])
        
        cooking_methods = st.multiselect("طرق تحضير الطعام المعتادة", [
            "سلق", "شوي", "قلي", "طهي بالبخار", "خبز", "طازج"
        ])

    st.markdown("### 🩺 الأعراض والتاريخ الصحي")
    with st.container():
        symptoms = st.multiselect(
            "الأعراض الحالية",
            options=[
                "التعب والإرهاق",
                "شحوب الجلد",
                "تساقط الشعر",
                "ضعف العضلات أو آلامها",
                "بطء التئام الجروح",
                "الصداع",
                "الدوخة",
                "تقصف الأظافر",
                "مشاكل في النوم"
            ],
            default=[]  # إضافة قيمة افتراضية فارغة
        )

        chronic_diseases = st.multiselect(
            "الأمراض المزمنة",
            options=[
                "السكري",
                "مشاكل الجهاز الهضمي",
                "مشاكل القلب",
                "مشاكل الكلى",
                "ضغط الدم",
                "الغدة الدرقية"
            ],
            default=[]  # إضافة قيمة افتراضية فارغة
        )

# إضافة التحقق من صحة المدخلات
def validate_inputs(data):
    if data["age"] <= 0:
        return False, "يرجى إدخال عمر صحيح"
    if data["weight"] <= 0:
        return False, "يرجى إدخال وزن صحيح"
    if data["height"] <= 0:
        return False, "يرجى إدخال طول صحيح"
    return True, ""

# تعريف المتغير supplements إذا لم يكن موجوداً
supplements = st.text_input("المكملات الغذائية المستخدمة حالياً", help="اكتب المكملات الغذائية التي تتناولها حالياً")

# تعريف التقرير الكامل قبل استخدامه
def generate_full_report(data, result, bmi, bmi_category):
    return f"""
    # تقرير التحليل الصحي والغذائي

    ## معلومات المريض
    * العمر: {data['age']} سنة
    * الجنس: {data['gender']}
    * الوزن: {data['weight']} كجم
    * الطول: {data['height']} سم
    * مؤشر كتلة الجسم: {bmi:.1f} ({bmi_category})

    ## تحليل الحالة الصحية
    {result['analysis']}

    ## تحليل الفيتامينات والمعادن
    {result['vitamin_analysis']}

    ## التوصيات والإرشادات
    {result['recommendations']}

    تم إنشاء هذا التقرير بواسطة نظام تحليل الحالة الغذائية
    تطوير: م. إبراهيم الجحيشي
    التاريخ: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    """

# ...existing code...

def show_analysis_results(data, result, bmi, bmi_category):
    """عرض نتائج التحليل بشكل متخصص وشامل"""
    try:
        # عرض التحليل العام
        st.markdown("<div class='section-header'>📊 التحليل العام</div>", unsafe_allow_html=True)
        st.markdown(result['analysis'], unsafe_allow_html=True)
        
        # عرض تحليل الفيتامينات
        st.markdown("<div class='section-header'>💊 تحليل الفيتامينات والمعادن</div>", unsafe_allow_html=True)
        
        vitamin_data = []
        for vitamin in result['vitamin_analysis']:
            status_color = "danger" if vitamin['status'] == "نقص" else "normal"
            vitamin_data.append({
                "الفيتامين": vitamin['name'],
                "الحالة": f"<span class='status-badge {status_color}'>{vitamin['status']}</span>",
                "التوصيات": vitamin['recommendations']
            })
        
        df = pd.DataFrame(vitamin_data)
        st.markdown(df.to_html(escape=False, index=False, classes='styled-table'), unsafe_allow_html=True)
        
        # عرض التوصيات العامة فقط
        st.markdown("<div class='section-header'>📋 التوصيات العامة</div>", unsafe_allow_html=True)
        st.markdown(result['recommendations'], unsafe_allow_html=True)
        
    except Exception as e:
        st.error(f"حدث خطأ في عرض النتائج: {str(e)}")
        st.error("يرجى المحاولة مرة أخرى أو الاتصال بالدعم الفني")

# إضافة وظائف تحليل جديدة
def get_bmi_health_impact(bmi):
    if bmi < 18.5:
        return "خطر نقص التغذية وضعف المناعة"
    elif bmi < 25:
        return "وزن مثالي يدعم الصحة العامة"
    elif bmi < 30:
        return "زيادة خطر الإصابة بأمراض القلب والسكري"
    else:
        return "خطر مرتفع للإصابة بالأمراض المزمنة"

def get_diet_health_impact(data):
    impacts = []
    if data['diet'] == "نباتي":
        impacts.append("خطر نقص فيتامين B12 والحديد")
    if data['vegetables_fruits'] in ["نادراً", "أحياناً"]:
        impacts.append("نقص محتمل في مضادات الأكسدة والألياف")
    return " | ".join(impacts) if impacts else "نظام غذائي متوازن"

# ...existing code...

# إضافة متغيرات جديدة للعلاج والأدوية
with col2:
    st.markdown("### 💊 الأدوية والعلاجات")
    medications = st.text_area(
        "الأدوية المستخدمة حالياً",
        help="اكتب الأدوية التي تتناولها حالياً",
        key="medications_input"
    )
    
    vegetables_fruits = st.select_slider(
        "تناول الخضروات والفواكه",
        options=["نادراً", "أحياناً", "بانتظام", "كثيراً"],
        value="بانتظام",
        key="vegetables_fruits_input"
    )
    
    dairy_meat = st.select_slider(
        "تناول منتجات الألبان واللحوم",
        options=["نادراً", "أحياناً", "بانتظام", "كثيراً"],
        value="بانتظام",
        key="dairy_meat_input"
    )

# زر إرسال البيانات
if st.button("تحليل الحالة الصحية", key="analyze_button"):
    try:
        # تجميع البيانات بشكل صحيح
        data = {
            "age": age,
            "gender": gender,
            "weight": weight,
            "height": height,
            "sun_exposure": sun_exposure,
            "activity_level": activity_level,
            "diet_type": diet_type,  # سيتم تحويله في الخادم إلى diet
            "symptoms": ", ".join(symptoms) if symptoms else "لا توجد أعراض",
            "chronic_diseases": ", ".join(chronic_diseases) if chronic_diseases else "لا توجد أمراض مزمنة",
            "medications": medications if medications else "",
            "vegetables_fruits": vegetables_fruits,
            "dairy_meat": dairy_meat,
            "supplements": supplements if supplements else "",
            "meals_info": {
                "count": meals_count,
                "breakfast": breakfast,
                "lunch": lunch,
                "dinner": dinner,
                "snacks": snacks
            },
            "sun_context": sun_context,
            "physical_activities": physical_activities,
            "exercise_duration": exercise_duration,
            "sleep_info": {
                "hours": sleep_hours,
                "quality": sleep_quality
            },
            "stress_level": stress_level,
            "meal_components": meal_components,
            "cooking_methods": cooking_methods
        }

        # التحقق من صحة المدخلات قبل الإرسال
        is_valid, error_message = validate_inputs(data)
        
        if not is_valid:
            st.error(error_message)
        else:
            with st.spinner('جاري تحليل البيانات... ⏳'):
                response = requests.post(
                    "http://127.0.0.1:8000/submit-symptoms/",
                    json=data,
                    timeout=60
                )
                
                if response.status_code == 200:
                    result = response.json()
                    st.success("✅ تم تحليل البيانات بنجاح!")
                    
                    bmi = data["weight"] / ((data["height"]/100) ** 2)
                    bmi_category = (
                        "نقص في الوزن" if bmi < 18.5
                        else "وزن طبيعي" if bmi < 25
                        else "زيادة في الوزن" if bmi < 30
                        else "سمنة"
                    )
                    
                    show_analysis_results(data, result, bmi, bmi_category)
                else:
                    st.error("❌ حدث خطأ في الاتصال بالخادم")

    except Exception as e:
        st.error(f"❌ حدث خطأ: {str(e)}")

# إضافة تذييل الصفحة
st.markdown("---")
st.markdown(
    """
   
    """, 
    unsafe_allow_html=True
)

# إضافة شعار المطور في الشريط الجانبي
with st.sidebar:
    st.markdown("### معلومات المطور")
    st.markdown("""
    - **المطور**:إبراهيم الجحيشي
    - **التخصص**: ذكاء اصطناعي وتحليل بيانات
    - **الإصدار**: 1.0.0
    """)
