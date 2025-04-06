from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import datetime

Base = declarative_base()

# جدول السيارات
class Car(Base):
    __tablename__ = 'cars'
    id = Column(Integer, primary_key=True)
    chassis_number = Column(String, unique=True)
    plate_number = Column(String, unique=True)
    car_type = Column(String)
    model = Column(String)
    year = Column(Integer)
    image_path = Column(String, nullable=True)
    status = Column(String, default="متوفرة")

# جدول طلبات الاستلام
class UserRequest(Base):
    __tablename__ = 'user_requests'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    car_id = Column(Integer)
    full_name = Column(String)
    phone_number = Column(String)
    delivery_location = Column(String)
    request_date = Column(DateTime, default=datetime.datetime.utcnow)

# إعداد قاعدة البيانات
engine = create_engine('sqlite:///stolen_cars.db')
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)

# دالة للبحث عن سيارة
def search_car(session, query):
    return session.query(Car).filter(
        (Car.chassis_number == query) | (Car.plate_number == query)
    ).first()

# دالة لإضافة بيانات السيارات الأولية
def populate_initial_data():
    session = Session()
    # إذا كانت قاعدة البيانات تحتوي على بيانات، لا تضيف مرة أخرى
    if session.query(Car).count() > 0:
        session.close()
        return

    # بيانات السيارات من القائمة
    cars = [
        Car(chassis_number="008444", plate_number="29738/4", car_type="اسكودا", model="", year=2012, image_path="images/image1.jpg"),
        Car(chassis_number="002634", plate_number="23553/3", car_type="اوتلاندر", model="", year=2005, image_path="images/image2.jpg"),
        Car(chassis_number="332223", plate_number="8574/5", car_type="تيدا", model="", year=2014, image_path=None),
        Car(chassis_number="586197", plate_number="8574/5", car_type="اسكودا", model="", year=2008, image_path=None),
        Car(chassis_number="000454", plate_number="95082/2", car_type="وكس واكن", model="", year=2008, image_path=None),
        Car(chassis_number="24183", plate_number="95082/2", car_type="وكس واكن", model="", year=2008, image_path=None),
        Car(chassis_number="7278352", plate_number="95082/2", car_type="وكس واكن", model="", year=2011, image_path=None),
        Car(chassis_number="169699", plate_number="95082/2", car_type="وكس واكن", model="", year=2011, image_path=None),
        Car(chassis_number="001693", plate_number="95082/2", car_type="وكس واكن", model="", year=2018, image_path=None),
        Car(chassis_number="0016546", plate_number="95082/2", car_type="وكس واكن", model="", year=2018, image_path=None),
        Car(chassis_number="289539", plate_number="12832/5", car_type="وكس واكن", model="", year=2019, image_path=None),
        Car(chassis_number="149883", plate_number="95082/2", car_type="رينو", model="", year=2015, image_path=None),
        Car(chassis_number="9051128", plate_number="20200/5", car_type="دي اكس دي", model="", year=2004, image_path=None),
        Car(chassis_number="001691", plate_number="20200/5", car_type="دي اكس دي", model="", year=2004, image_path=None),
        Car(chassis_number="06478", plate_number="20200/5", car_type="اكسنت", model="", year=2004, image_path=None),
        Car(chassis_number="3600046", plate_number="20200/5", car_type="اكسنت", model="", year=2004, image_path=None),
        Car(chassis_number="052798", plate_number="93557/2", car_type="جورج", model="", year=2004, image_path=None),
    ]

    # إضافة السجلات مع التحقق من التكرارات
    for car in cars:
        try:
            # تحقق مما إذا كان رقم اللوحة موجودًا بالفعل
            existing_car = session.query(Car).filter_by(plate_number=car.plate_number).first()
            if existing_car:
                print(f"تم تخطي السيارة برقم اللوحة {car.plate_number} لأنها موجودة بالفعل.")
                continue
            session.add(car)
            session.commit()
        except Exception as e:
            session.rollback()
            print(f"خطأ أثناء إضافة السيارة برقم اللوحة {car.plate_number}: {str(e)}")

    session.close()