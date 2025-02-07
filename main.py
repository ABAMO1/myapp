from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import sqlalchemy
from sqlalchemy import create_engine, Column, Integer, String, Text
from sqlalchemy.orm import declarative_base, sessionmaker
import aiohttp
import databases
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.naive_bayes import MultinomialNB
import numpy as np
import joblib
import logging
from sklearn.metrics import accuracy_score, classification_report
import pandas as pd
from datetime import datetime
import os

# تهيئة التسجيل
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# تحديث مفتاح API ونقطة النهاية
GEMINI_API_KEY = "AIzaSyB3JjqPnCOn--7hO-TBRnrd7h_qPBKaaTM"
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent"

# تعريف دوال التحليل قبل استخدامها
def analyze_nutrient_status(data, nutrient_type):
    """تحليل حالة المغذيات"""
    risk_factors = {
        "vitamin_e": [
            data['vegetables_fruits'] in ["نادراً", "أحياناً"],
            not any("زيوت نباتية" in comp for comp in data['meal_components'])
        ],
        "vitamin_k": [
            data['vegetables_fruits'] in ["نادراً", "أحياناً"],
            not any("خضروات طازجة" in comp for comp in data['meal_components'])
        ],
        "vitamin_c": [
            data['vegetables_fruits'] in ["نادراً", "أحياناً"],
            not any(x in data['meal_components'] for x in ["فواكه", "خضروات طازجة"])
        ],
        "folate": [
            data['vegetables_fruits'] in ["نادراً", "أحياناً"],
            not any("خضروات" in comp for comp in data['meal_components'])
        ],
        "potassium": [
            data['vegetables_fruits'] in ["نادراً", "أحياناً"],
            "ضعف العضلات" in data['symptoms']
        ],
        "manganese": [
            not any(x in data['meal_components'] for x in ["حبوب كاملة", "مكسرات"]),
            data['vegetables_fruits'] in ["نادراً", "أحياناً"]
        ],
        "copper": [
            data['diet_type'] == "نباتي",
            not any("مكسرات" in comp for comp in data['meal_components'])
        ],
        "zinc": [
            "بطء التئام الجروح" in data['symptoms'],
            data['dairy_meat'] in ["نادراً", "أحياناً"]
        ],
        "selenium": [
            data['diet_type'] == "نباتي",
            not any("أسماك" in comp for comp in data['meal_components'])
        ],
        "iodine": [
            data['dairy_meat'] in ["نادراً", "أحياناً"],
            not any("أسماك" in comp for comp in data['meal_components'])
        ]
    }
    
    if nutrient_type in risk_factors:
        return "نقص" if any(risk_factors[nutrient_type]) else "طبيعي"
    return "طبيعي"

# باقي الدوال المساعدة
def analyze_vitamin_d_status(data):
    """تحليل حالة فيتامين D"""
    risk_factors = [
        data['sun_exposure'] < 0.5,
        data['dairy_meat'] in ["نادراً", "أحياناً"],
        data['sun_context'] == "محدود (داخل المباني معظم الوقت)",
        "ضعف العضلات أو آلامها" in data['symptoms']
    ]
    return "نقص شديد" if sum(risk_factors) >= 3 else "نقص" if sum(risk_factors) >= 2 else "طبيعي"

def analyze_vitamin_a_status(data):
    """تحليل حالة فيتامين A"""
    risk_factors = [
        data['vegetables_fruits'] in ["نادراً", "أحياناً"],
        "مشاكل في الرؤية" in data['symptoms'],
        "جفاف الجلد" in data['symptoms'],
        not any(x in data['meal_components'] for x in ["خضروات طازجة", "فواكه"])
    ]
    return "نقص شديد" if sum(risk_factors) >= 3 else "نقص" if sum(risk_factors) >= 2 else "طبيعي"

def analyze_b_vitamins_status(data, vitamin_type):
    """تحليل حالة فيتامينات B"""
    risk_factors = {
        "b1": [
            data['diet_type'] == "نباتي",
            not any(x in data['meal_components'] for x in ["حبوب كاملة", "بقوليات"]),
            "التعب والإرهاق" in data['symptoms']
        ],
        "b2": [
            data['dairy_meat'] in ["نادراً", "أحياناً"],
            "تشقق زوايا الفم" in data['symptoms']
        ],
        "b3": [
            data['diet_type'] == "نباتي",
            "الصداع" in data['symptoms']
        ],
        "b6": [
            data['vegetables_fruits'] in ["نادراً", "أحياناً"],
            "تشنجات عضلية" in data['symptoms']
        ]
    }
    
    if vitamin_type in risk_factors:
        factors = risk_factors[vitamin_type]
        return "نقص" if sum(factors) >= 2 else "طبيعي"
    return "طبيعي"

def analyze_b12_status(data):
    risk_factors = [
        data['diet_type'] in ["نباتي", "نباتي مع أسماك"],
        data['dairy_meat'] in ["نادراً", "أحياناً"],
        "التعب والإرهاق" in data['symptoms'],
        "الدوخة" in data['symptoms']
    ]
    return "نقص شديد" if sum(risk_factors) >= 3 else "نقص" if sum(risk_factors) >= 2 else "طبيعي"

def analyze_iron_status(data):
    risk_factors = [
        data['diet_type'] == "نباتي",
        "شحوب الجلد" in data['symptoms'],
        "التعب والإرهاق" in data['symptoms'],
        data['dairy_meat'] in ["نادراً", "أحياناً"]
    ]
    return "نقص شديد" if sum(risk_factors) >= 3 else "نقص" if sum(risk_factors) >= 2 else "طبيعي"

def analyze_calcium_status(data):
    risk_factors = [
        data['dairy_meat'] in ["نادراً", "أحياناً"],
        data['diet_type'] == "نباتي",
        "ضعف العضلات أو آلامها" in data['symptoms'],
        not any("منتجات ألبان" in comp for comp in data['meal_components'])
    ]
    return "نقص شديد" if sum(risk_factors) >= 3 else "نقص" if sum(risk_factors) >= 2 else "طبيعي"

def analyze_mineral_status(data, mineral_type):
    """تحليل حالة المعادن"""
    risk_factors = {
        "magnesium": [
            "ضعف العضلات" in data['symptoms'],
            "تشنجات عضلية" in data['symptoms'],
            data['vegetables_fruits'] in ["نادراً", "أحياناً"]
        ],
        "zinc": [
            "بطء التئام الجروح" in data['symptoms'],
            data['dairy_meat'] in ["نادراً", "أحياناً"],
            "تساقط الشعر" in data['symptoms']
        ],
        "selenium": [
            data['diet_type'] == "نباتي",
            not any("أسماك" in comp for comp in data['meal_components'])
        ],
        "copper": [
            "فقر الدم" in data['symptoms'],
            "ضعف العظام" in data['symptoms']
        ]
    }

    if mineral_type in risk_factors:
        factors = risk_factors[mineral_type]
        return "نقص" if sum(factors) >= 2 else "طبيعي"
    return "طبيعي"

def get_b12_recommendations(data):
    if data['diet_type'] in ["نباتي", "نباتي مع أسماك"]:
        return """
        - تناول مكملات B12 بانتظام (1000 ميكروغرام يومياً)
        - إضافة الأطعمة المدعمة بفيتامين B12
        - متابعة مستويات B12 في الدم بشكل دوري
        """
    return "الحفاظ على تناول اللحوم والأسماك والبيض بانتظام"

def get_iron_recommendations(data):
    if analyze_iron_status(data) in ["نقص", "نقص شديد"]:
        return """
        - تناول اللحوم الحمراء 2-3 مرات أسبوعياً
        - دمج مصادر فيتامين C مع الأطعمة الغنية بالحديد
        - تجنب شرب الشاي والقهوة مع الوجبات
        - استشارة الطبيب لتقييم الحاجة للمكملات
        """
    return "الحفاظ على النظام الغذائي المتوازن الحالي"

def get_calcium_recommendations(data):
    if analyze_calcium_status(data) in ["نقص", "نقص شديد"]:
        return """
        - زيادة تناول منتجات الألبان قليلة الدسم
        - تناول الخضروات الورقية الداكنة
        - إضافة السردين والسلمون مع العظام
        - النظر في تناول مكملات الكالسيوم مع فيتامين D
        """
    return "الاستمرار في تناول المصادر الجيدة للكالسيوم في النظام الغذائي الحالي"

# إنشاء تطبيق FastAPI
app = FastAPI()

# تهيئة قاعدة البيانات
DATABASE_URL = "sqlite:///./test.db"
database = databases.Database(DATABASE_URL)
metadata = sqlalchemy.MetaData()

# تعريف جدول البيانات
Base = declarative_base()

class UserInput(Base):
    __tablename__ = "user_inputs"
    id = Column(Integer, primary_key=True, index=True)
    user_input = Column(Text, index=True)
    gemini_output = Column(Text, index=True)

engine = create_engine(DATABASE_URL)
Base.metadata.create_all(bind=engine)

# نموذج البيانات المستلمة من المستخدم
class SymptomInput(BaseModel):
    age: int
    gender: str
    weight: float
    height: float
    sun_exposure: float
    activity_level: str
    diet_type: str  # تم تغيير diet إلى diet_type
    symptoms: str
    chronic_diseases: str
    medications: str
    vegetables_fruits: str
    dairy_meat: str
    supplements: str
    meals_info: dict
    sun_context: str
    physical_activities: list
    exercise_duration: int
    sleep_info: dict
    stress_level: str
    meal_components: list
    cooking_methods: list

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Code to run on startup
    await database.connect()
    yield
    # Code to run on shutdown
    await database.disconnect()

# إنشاء تطبيق FastAPI مع lifespan event handler
app = FastAPI(lifespan=lifespan)

# نقطة النهاية لاستقبال البيانات من المستخدم
@app.post("/submit-symptoms/")
async def submit_symptoms(symptom_input: SymptomInput):
    try:
        input_data = symptom_input.dict()
        
        # حساب مؤشر كتلة الجسم
        bmi = input_data['weight'] / ((input_data['height']/100) ** 2)
        bmi_category = (
            "نقص في الوزن" if bmi < 18.5
            else "وزن طبيعي" if bmi < 25
            else "زيادة في الوزن" if bmi < 30
            else "سمنة"
        )
        # إنشاء التحليل العام
        general_analysis = f"""
        ### التحليل العام للحالة الصحية
        - مؤشر كتلة الجسم: {bmi:.1f} ({bmi_category})
        - العمر: {input_data['age']} سنة
        - الجنس: {input_data['gender']}
        
        ### تحليل نمط الحياة
        - مستوى النشاط البدني: {input_data['activity_level']}
        - التعرض للشمس: {input_data['sun_exposure']} ساعات يومياً
        - جودة النوم: {input_data['sleep_info']['quality']}
        - مستوى التوتر: {input_data['stress_level']}
        
        ### تحليل النظام الغذائي
        - نوع النظام: {input_data['diet_type']}
        - تناول الخضروات والفواكه: {input_data['vegetables_fruits']}
        - تناول البروتينات: {input_data['dairy_meat']}
        """

        # تحليل الفيتامينات والمعادن الشامل
        vitamin_analysis = [
            {
                "name": "فيتامين D (كالسيفيرول)",
                "status": analyze_vitamin_d_status(input_data),
                "recommendations": "التعرض للشمس 15-20 دقيقة يومياً، تناول الأسماك الدهنية، صفار البيض، زيت كبد السمك"
            },
            {
                "name": "فيتامين A (ريتينول)",
                "status": analyze_vitamin_a_status(input_data),
                "recommendations": "تناول الجزر، البطاطا الحلوة، السبانخ، المشمش، الكبد"
            },
            {
                "name": "فيتامين E (توكوفيرول)",
                "status": analyze_nutrient_status(input_data, "vitamin_e"),
                "recommendations": "تناول المكسرات، البذور، الأفوكادو، زيت الزيتون، السبانخ"
            },
            {
                "name": "فيتامين K",
                "status": analyze_nutrient_status(input_data, "vitamin_k"),
                "recommendations": "تناول الخضروات الورقية الخضراء، البروكلي، الملفوف"
            },
            {
                "name": "فيتامين C (حمض الأسكوربيك)",
                "status": analyze_nutrient_status(input_data, "vitamin_c"),
                "recommendations": "تناول الحمضيات، الفلفل، الطماطم، البروكلي، الفراولة"
            },
            {
                "name": "فيتامين B1 (ثيامين)",
                "status": analyze_b_vitamins_status(input_data, "b1"),
                "recommendations": "تناول الحبوب الكاملة، البقوليات، المكسرات، اللحوم"
            },
            {
                "name": "فيتامين B2 (ريبوفلافين)",
                "status": analyze_b_vitamins_status(input_data, "b2"),
                "recommendations": "تناول منتجات الألبان، البيض، اللحوم، الخضروات الورقية"
            },
            {
                "name": "فيتامين B3 (نياسين)",
                "status": analyze_b_vitamins_status(input_data, "b3"),
                "recommendations": "تناول اللحوم، الأسماك، البذور، الفول السوداني"
            },
            {
                "name": "فيتامين B6 (بيريدوكسين)",
                "status": analyze_b_vitamins_status(input_data, "b6"),
                "recommendations": "تناول الموز، البطاطا، الدجاج، الأسماك، الحمص"
            },
            {
                "name": "فيتامين B12 (كوبالامين)",
                "status": analyze_b12_status(input_data),
                "recommendations": get_b12_recommendations(input_data)
            },
            {
                "name": "حمض الفوليك",
                "status": analyze_nutrient_status(input_data, "folate"),
                "recommendations": "تناول الخضروات الورقية، البقوليات، الحبوب المدعمة"
            },
            {
                "name": "الحديد",
                "status": analyze_iron_status(input_data),
                "recommendations": get_iron_recommendations(input_data)
            },
            {
                "name": "الكالسيوم",
                "status": analyze_calcium_status(input_data),
                "recommendations": get_calcium_recommendations(input_data)
            },
            {
                "name": "المغنيسيوم",
                "status": analyze_mineral_status(input_data, "magnesium"),
                "recommendations": "تناول المكسرات، البذور، البقوليات، الخضروات الورقية الداكنة"
            },
            {
                "name": "الزنك",
                "status": analyze_mineral_status(input_data, "zinc"),
                "recommendations": "تناول المحار، اللحوم، البذور، المكسرات"
            },
            {
                "name": "السيلينيوم",
                "status": analyze_mineral_status(input_data, "selenium"),
                "recommendations": "تناول المكسرات البرازيلية، الأسماك، البيض، الحبوب الكاملة"
            },
            {
                "name": "النحاس",
                "status": analyze_mineral_status(input_data, "copper"),
                "recommendations": "تناول الكبد، المحار، المكسرات، البذور"
            },
            {
                "name": "المنغنيز",
                "status": analyze_mineral_status(input_data, "manganese"),
                "recommendations": "تناول المكسرات، الحبوب الكاملة، البقوليات، الشاي"
            },
            {
                "name": "البوتاسيوم",
                "status": analyze_mineral_status(input_data, "potassium"),
                "recommendations": "تناول الموز، البطاطا، الخضروات الورقية، الحمضيات"
            },
            {
                "name": "اليود",
                "status": analyze_mineral_status(input_data, "iodine"),
                "recommendations": "استخدام الملح المدعم باليود، تناول الأعشاب البحرية، الأسماك"
            }
        ]

        # التوصيات العامة
        recommendations = """
        ### التوصيات العامة
        1. تنظيم الوجبات الغذائية وتنويع مصادر الغذاء
        2. تناول 5 حصص من الخضروات والفواكه يومياً
        3. شرب 8-10 أكواب من الماء يومياً
        4. ممارسة الرياضة لمدة 30 دقيقة على الأقل يومياً
        5. الحصول على قسط كافٍ من النوم (7-9 ساعات)
        6. تقليل مستويات التوتر من خلال ممارسة تمارين الاسترخاء
        7. تناول وجبات متوازنة تشمل جميع العناصر الغذائية
        8. المحافظة على وزن صحي ومؤشر كتلة جسم مثالي
        """

        return {
            "status": "success",
            "analysis": general_analysis,
            "vitamin_analysis": vitamin_analysis,
            "recommendations": recommendations
        }

    except Exception as e:
        logger.error(f"Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# دوال تحليل الفيتامينات المحسنة
def analyze_vitamin_d_status(data):
    risk_factors = [
        data['sun_exposure'] < 0.5,
        data['dairy_meat'] in ["نادراً", "أحياناً"],
        data['sun_context'] == "محدود (داخل المباني معظم الوقت)",
        "ضعف العضلات أو آلامها" in data['symptoms']
    ]
    return "نقص شديد" if sum(risk_factors) >= 3 else "نقص" if sum(risk_factors) >= 2 else "طبيعي"

def analyze_b12_status(data):
    risk_factors = [
        data['diet_type'] in ["نباتي", "نباتي مع أسماك"],
        data['dairy_meat'] in ["نادراً", "أحياناً"],
        "التعب والإرهاق" in data['symptoms'],
        "الدوخة" in data['symptoms']
    ]
    return "نقص شديد" if sum(risk_factors) >= 3 else "نقص" if sum(risk_factors) >= 2 else "طبيعي"

def analyze_iron_status(data):
    risk_factors = [
        data['diet_type'] == "نباتي",
        "شحوب الجلد" in data['symptoms'],
        "التعب والإرهاق" in data['symptoms'],
        data['dairy_meat'] in ["نادراً", "أحياناً"]
    ]
    return "نقص شديد" if sum(risk_factors) >= 3 else "نقص" if sum(risk_factors) >= 2 else "طبيعي"

def analyze_calcium_status(data):
    risk_factors = [
        data['dairy_meat'] in ["نادراً", "أحياناً"],
        data['diet_type'] == "نباتي",
        "ضعف العضلات أو آلامها" in data['symptoms'],
        not any("منتجات ألبان" in comp for comp in data['meal_components'])
    ]
    return "نقص شديد" if sum(risk_factors) >= 3 else "نقص" if sum(risk_factors) >= 2 else "طبيعي"

def get_b12_recommendations(data):
    if data['diet_type'] in ["نباتي", "نباتي مع أسماك"]:
        return """
        - تناول مكملات B12 بانتظام (1000 ميكروغرام يومياً)
        - إضافة الأطعمة المدعمة بفيتامين B12
        - متابعة مستويات B12 في الدم بشكل دوري
        """
    return "الحفاظ على تناول اللحوم والأسماك والبيض بانتظام"

def get_iron_recommendations(data):
    if analyze_iron_status(data) in ["نقص", "نقص شديد"]:
        return """
        - تناول اللحوم الحمراء 2-3 مرات أسبوعياً
        - دمج مصادر فيتامين C مع الأطعمة الغنية بالحديد
        - تجنب شرب الشاي والقهوة مع الوجبات
        - استشارة الطبيب لتقييم الحاجة للمكملات
        """
    return "الحفاظ على النظام الغذائي المتوازن الحالي"

def get_calcium_recommendations(data):
    if analyze_calcium_status(data) in ["نقص", "نقص شديد"]:
        return """
        - زيادة تناول منتجات الألبان قليلة الدسم
        - تناول الخضروات الورقية الداكنة
        - إضافة السردين والسلمون مع العظام
        - النظر في تناول مكملات الكالسيوم مع فيتامين D
        """
    return "الاستمرار في تناول المصادر الجيدة للكالسيوم في النظام الغذائي الحالي"

# إضافة دوال تحليل الفيتامينات المفقودة
def analyze_vitamin_a_status(data):
    """تحليل حالة فيتامين A"""
    risk_factors = [
        data['vegetables_fruits'] in ["نادراً", "أحياناً"],
        "مشاكل في الرؤية" in data['symptoms'],
        "جفاف الجلد" in data['symptoms'],
        not any(x in data['meal_components'] for x in ["خضروات طازجة", "فواكه"])
    ]
    return "نقص شديد" if sum(risk_factors) >= 3 else "نقص" if sum(risk_factors) >= 2 else "طبيعي"

def analyze_b_vitamins_status(data, vitamin_type):
    """تحليل حالة فيتامينات B"""
    risk_factors = {
        "b1": [
            data['diet_type'] == "نباتي",
            not any(x in data['meal_components'] for x in ["حبوب كاملة", "بقوليات"]),
            "التعب والإرهاق" in data['symptoms']
        ],
        "b2": [
            data['dairy_meat'] in ["نادراً", "أحياناً"],
            "تشقق زوايا الفم" in data['symptoms']
        ],
        "b3": [
            data['diet_type'] == "نباتي",
            "الصداع" in data['symptoms']
        ],
        "b6": [
            data['vegetables_fruits'] in ["نادراً", "أحياناً"],
            "تشنجات عضلية" in data['symptoms']
        ]
    }
    
    if vitamin_type in risk_factors:
        factors = risk_factors[vitamin_type]
        return "نقص" if sum(factors) >= 2 else "طبيعي"
    return "طبيعي"

def analyze_mineral_status(data, mineral_type):
    """تحليل حالة المعادن"""
    risk_factors = {
        "magnesium": [
            "ضعف العضلات" in data['symptoms'],
            "تشنجات عضلية" in data['symptoms'],
            data['vegetables_fruits'] in ["نادراً", "أحياناً"]
        ],
        "zinc": [
            "بطء التئام الجروح" in data['symptoms'],
            data['dairy_meat'] in ["نادراً", "أحياناً"],
            "تساقط الشعر" in data['symptoms']
        ],
        "selenium": [
            data['diet_type'] == "نباتي",
            not any("أسماك" in comp for comp in data['meal_components'])
        ],
        "copper": [
            "فقر الدم" in data['symptoms'],
            "ضعف العظام" in data['symptoms']
        ]
    }

    if mineral_type in risk_factors:
        factors = risk_factors[mineral_type]
        return "نقص" if sum(factors) >= 2 else "طبيعي"
    return "طبيعي"

class ModelTraining:
    def __init__(self):
        self.model = None
        self.vectorizer = None
        self.training_history = []

    async def preprocess_data(self, data):
        """معالجة البيانات وتحويلها إلى تنسيق مناسب للتدريب"""
        inputs = []
        outputs = []
        
        for item in data:
            # تقسيم النص إلى أقسام محددة
            text = item["gemini_output"]
            sections = text.split('\n\n')
            
            # استخراج المعلومات المهمة
            vitamin_info = ""
            for section in sections:
                if "فيتامين" in section or "معدن" in section:  # تصحيح الخطأ هنا
                    vitamin_info += section + "\n"
            
            inputs.append(item["user_input"])
            outputs.append(vitamin_info.strip())
        
        return inputs, outputs

    async def train_and_evaluate(self, X, y):
        """تدريب النموذج وتقييمه"""
        # تقسيم البيانات
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        # تحويل النصوص
        self.vectorizer = CountVectorizer(max_features=5000)
        X_train_vec = self.vectorizer.fit_transform(X_train)
        X_test_vec = self.vectorizer.transform(X_test)
        
        # تدريب النموذج
        self.model = MultinomialNB()
        self.model.fit(X_train_vec, y_train)
        
        # تقييم النموذج
        y_pred = self.model.predict(X_test_vec)
        accuracy = accuracy_score(y_test, y_pred)
        
        # حفظ نتائج التدريب
        training_result = {
            'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'accuracy': accuracy,
            'num_samples': len(X),
            'model_params': self.model.get_params()
        }
        self.training_history.append(training_result)
        
        return accuracy, classification_report(y_test, y_pred)

# تحديث نقطة نهاية التدريب
@app.post("/train-model/")
async def train_model():
    try:
        # استرداد البيانات
        query = UserInput.__table__.select()
        results = await database.fetch_all(query)
        
        if len(results) < 10:  # التحقق من وجود بيانات كافية
            raise HTTPException(
                status_code=400,
                detail="عدد غير كافٍ من البيانات للتدريب. مطلوب 10 عينات على الأقل."
            )
        
        # تهيئة نموذج التدريب
        trainer = ModelTraining()
        
        # معالجة البيانات
        inputs, outputs = await trainer.preprocess_data(results)
        
        # تدريب وتقييم النموذج
        accuracy, report = await trainer.train_and_evaluate(inputs, outputs)
        
        # حفظ النموذج
        model_filename = f"model_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pkl"
        vectorizer_filename = f"vectorizer_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pkl"
        
        joblib.dump(trainer.model, model_filename)
        joblib.dump(trainer.vectorizer, vectorizer_filename)
        
        # تحضير التقرير
        training_report = {
            "status": "success",
            "accuracy": float(accuracy),
            "num_samples": len(inputs),
            "model_file": model_filename,
            "vectorizer_file": vectorizer_filename,
            "classification_report": report,
            "latest_training": trainer.training_history[-1]
        }
        
        logger.info(f"Training completed successfully: {training_report}")
        return training_report

    except Exception as e:
        logger.error(f"Training error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# إضافة نقطة نهاية جديدة لتقييم النموذج
@app.post("/evaluate-model/")
async def evaluate_model(text: str):
    try:
        # تحميل أحدث نموذج
        model_files = [f for f in os.listdir('.') if f.startswith('model_')]
        if not model_files:
            raise HTTPException(status_code=404, detail="لم يتم العثور على نموذج مدرب")
        
        latest_model = max(model_files)
        latest_vectorizer = max([f for f in os.listdir('.') if f.startswith('vectorizer_')])
        
        model = joblib.load(latest_model)
        vectorizer = joblib.load(latest_vectorizer)
        
        # تحويل النص وتوقع النتيجة
        text_vec = vectorizer.transform([text])
        prediction = model.predict(text_vec)[0]
        
        return {
            "status": "success",
            "prediction": prediction,
            "model_used": latest_model
        }

    except Exception as e:
        logger.error(f"Evaluation error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))