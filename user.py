from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database import Session, search_car, UserRequest, Car
import datetime
from admin import ADMIN_IDS  # استيراد قائمة الأدمن

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "مرحبًا! أدخل رقم الشاسيه أو رقم لوحة السيارة للبحث عن سيارتك."
    )
    return 0  # الانتقال إلى حالة البحث

async def search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.message.text
    print(f"Search triggered with query: {query}")  # تصحيح أخطاء
    session = Session()

    car = search_car(session, query)
    if car:
        message = (
            f"تم العثور على سيارتك!\n"
            f"نوع السيارة: {car.car_type}\n"
            f"الموديل: {car.model}\n"
            f"سنة الصنع: {car.year}\n"
            f"رقم الشاسيه: {car.chassis_number}\n"
            f"رقم اللوحة: {car.plate_number}\n"
        )
        if car.image_path:
            try:
                await update.message.reply_photo(photo=open(car.image_path, 'rb'), caption=message)
            except FileNotFoundError:
                await update.message.reply_text(message + "\n(الصورة غير متوفرة حاليًا)")
        else:
            await update.message.reply_text(message)

        keyboard = [
            [InlineKeyboardButton("تقديم طلب استلام", callback_data=f"request_{car.id}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("هل ترغب في تقديم طلب استلام؟", reply_markup=reply_markup)
        session.close()
        return 1  # الانتقال إلى حالة طلب الاستلام
    else:
        await update.message.reply_text("لم يتم العثور على سيارتك بعد.")
        session.close()
        return 0  # البقاء في حالة البحث

async def request_car(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    car_id = int(query.data.split("_")[1])
    context.user_data['car_id'] = car_id
    await query.message.reply_text(
        "يرجى إدخال المعلومات التالية:\n"
        "الاسم الكامل:\n"
        "رقم الهاتف:\n"
        "موقع الاستلام:\n"
        "اكتب كل معلومة في سطر منفصل."
    )
    return 2  # الانتقال إلى حالة حفظ الطلب

async def save_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = update.message.text.split("\n")
    if len(user_input) != 3:
        await update.message.reply_text("يرجى إدخال المعلومات بشكل صحيح (3 أسطر).")
        return 2  # البقاء في حالة إدخال البيانات

    full_name, phone_number, delivery_location = user_input
    user_id = update.message.from_user.id
    car_id = context.user_data.get('car_id')

    session = Session()
    request = UserRequest(
        user_id=user_id,
        car_id=car_id,
        full_name=full_name,
        phone_number=phone_number,
        delivery_location=delivery_location,
        request_date=datetime.datetime.utcnow()
    )
    session.add(request)

    # تحديث حالة السيارة
    car = session.query(Car).filter_by(id=car_id).first()
    car.status = "تم استلامها"
    session.commit()

    # إرسال إشعار إلى الأدمن
    request_message = (
        "طلب استلام جديد:\n"
        f"الاسم الكامل: {full_name}\n"
        f"رقم الهاتف: {phone_number}\n"
        f"موقع الاستلام: {delivery_location}\n"
        f"رقم الشاسيه: {car.chassis_number}\n"
        f"رقم اللوحة: {car.plate_number}\n"
        f"تاريخ الطلب: {request.request_date}"
    )
    for admin_id in ADMIN_IDS:
        try:
            await context.bot.send_message(chat_id=admin_id, text=request_message)
        except Exception as e:
            print(f"Failed to send message to admin {admin_id}: {str(e)}")

    session.close()

    await update.message.reply_text("تم تقديم طلب الاستلام بنجاح! سيتم التواصل معك قريبًا.")
    context.user_data.pop('car_id', None)
    return 0  # العودة إلى حالة البحث