import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler,
    ConversationHandler
)
from database import Session, Car

# استخدام متغير بيئي لتخزين معرفات المسؤولين
ADMIN_IDS = list(map(int, os.environ.get('ADMIN_IDS', '#########').split(',')))

# حالات المحادثة
CHOOSE_ACTION, ADD_CAR, EDIT_CAR_SEARCH, EDIT_CAR, DELETE_CAR = range(5)

def is_admin(user_id):
    """التحقق مما إذا كان المستخدم مسؤولاً"""
    return user_id in ADMIN_IDS

def create_admin_keyboard():
    """إنشاء لوحة مفاتيح المسؤول"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("إضافة سيارة", callback_data="addcar")],
        [InlineKeyboardButton("تعديل سيارة", callback_data="editcar")],
        [InlineKeyboardButton("حذف سيارة", callback_data="deletecar")],
        [InlineKeyboardButton("عرض جميع السيارات", callback_data="listcars")]
    ])

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """عرض لوحة التحكم الرئيسية للمسؤول"""
    user_id = update.message.from_user.id
    if not is_admin(user_id):
        await update.message.reply_text("عذرًا، هذا الأمر مخصص للأدمن فقط.")
        return ConversationHandler.END

    await update.message.reply_text("مرحبًا بالأدمن! اختر إجراء:", reply_markup=create_admin_keyboard())
    return CHOOSE_ACTION

async def admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة الاستجابات لأزرار لوحة التحكم"""
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    if not is_admin(user_id):
        await query.message.reply_text("عذرًا، هذا الأمر مخصص للأدمن فقط.")
        return ConversationHandler.END

    action = query.data
    if action == "addcar":
        await query.message.reply_text(
            "يرجى إدخال بيانات السيارة بالشكل التالي:\n"
            "رقم الشاسيه:\n"
            "رقم اللوحة:\n"
            "نوع السيارة:\n"
            "الموديل:\n"
            "سنة الصنع:\n"
            "مسار الصورة (اختياري):\n"
            "اكتب كل معلومة في سطر منفصل."
        )
        return ADD_CAR
    elif action == "editcar":
        await query.message.reply_text("أدخل رقم الشاسيه أو رقم اللوحة للسيارة التي تريد تعديلها:")
        return EDIT_CAR_SEARCH
    elif action == "deletecar":
        await query.message.reply_text("أدخل رقم الشاسيه أو رقم اللوحة للسيارة التي تريد حذفها:")
        return DELETE_CAR
    elif action == "listcars":
        await list_cars(query.message)
        return CHOOSE_ACTION

async def list_cars(message):
    """عرض قائمة جميع السيارات"""
    session = Session()
    cars = session.query(Car).all()
    if not cars:
        await message.reply_text("لا توجد سيارات في قاعدة البيانات.")
    else:
        car_list = ["قائمة السيارات:"]
        for car in cars:
            car_list.append(
                f"ID: {car.id}\n"
                f"نوع السيارة: {car.car_type}\n"
                f"رقم الشاسيه: {car.chassis_number}\n"
                f"رقم اللوحة: {car.plate_number}\n"
                f"سنة الصنع: {car.year}\n"
                f"الحالة: {car.status}\n"
                "-----------------"
            )
        await message.reply_text("\n\n".join(car_list))
    session.close()

async def add_car(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """إضافة سيارة جديدة إلى قاعدة البيانات"""
    user_id = update.message.from_user.id
    if not is_admin(user_id):
        await update.message.reply_text("عذرًا، هذا الأمر مخصص للأدمن فقط.")
        return ConversationHandler.END

    user_input = update.message.text.split("\n")
    if len(user_input) < 5:
        await update.message.reply_text("يرجى إدخال جميع المعلومات المطلوبة.")
        return ADD_CAR

    chassis_number, plate_number, car_type, model, year = user_input[:5]
    image_path = user_input[5] if len(user_input) > 5 else None

    # التحقق من صحة الإدخال
    if not all([chassis_number, plate_number, car_type, model, year]):
        await update.message.reply_text("جميع الحقول مطلوبة باستثناء مسار الصورة.")
        return ADD_CAR

    try:
        year = int(year)
    except ValueError:
        await update.message.reply_text("سنة الصنع يجب أن تكون رقمًا.")
        return ADD_CAR

    session = Session()
    try:
        new_car = Car(
            chassis_number=chassis_number,
            plate_number=plate_number,
            car_type=car_type,
            model=model,
            year=year,
            image_path=image_path
        )
        session.add(new_car)
        session.commit()
        await update.message.reply_text("تم إضافة السيارة بنجاح!")
    except Exception as e:
        session.rollback()
        await update.message.reply_text(f"حدث خطأ أثناء الإضافة: {str(e)}")
    finally:
        session.close()

    await update.message.reply_text("اختر إجراء آخر:", reply_markup=create_admin_keyboard())
    return CHOOSE_ACTION

async def edit_car_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """البحث عن سيارة للتعديل"""
    user_id = update.message.from_user.id
    if not is_admin(user_id):
        await update.message.reply_text("عذرًا، هذا الأمر مخصص للأدمن فقط.")
        return ConversationHandler.END

    query = update.message.text
    session = Session()
    car = session.query(Car).filter(
        (Car.chassis_number == query) | (Car.plate_number == query)
    ).first()
    if car:
        context.user_data['car_id'] = car.id
        await update.message.reply_text(
            f"تم العثور على السيارة. أدخل البيانات الجديدة:\n"
            f"رقم الشاسيه: {car.chassis_number}\n"
            f"رقم اللوحة: {car.plate_number}\n"
            f"نوع السيارة: {car.car_type}\n"
            f"الموديل: {car.model}\n"
            f"سنة الصنع: {car.year}\n"
            f"مسار الصورة (اختياري): {car.image_path or ''}\n"
            "اكتب كل معلومة في سطر منفصل. اترك السطر فارغًا إذا لم ترغب في تغيير القيمة."
        )
        session.close()
        return EDIT_CAR
    else:
        await update.message.reply_text("لم يتم العثور على السيارة.")
        session.close()
        await update.message.reply_text("اختر إجراء آخر:", reply_markup=create_admin_keyboard())
        return CHOOSE_ACTION

async def edit_car(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """تعديل بيانات السيارة"""
    user_id = update.message.from_user.id
    if not is_admin(user_id):
        await update.message.reply_text("عذرًا، هذا الأمر مخصص للأدمن فقط.")
        return ConversationHandler.END

    user_input = update.message.text.split("\n")
    car_id = context.user_data.get('car_id')

    session = Session()
    car = session.query(Car).filter_by(id=car_id).first()
    if not car:
        await update.message.reply_text("لم يتم العثور على السيارة.")
        session.close()
        return CHOOSE_ACTION

    # تحديث البيانات إذا تم إدخالها
    if user_input[0]: car.chassis_number = user_input[0]
    if len(user_input) > 1 and user_input[1]: car.plate_number = user_input[1]
    if len(user_input) > 2 and user_input[2]: car.car_type = user_input[2]
    if len(user_input) > 3 and user_input[3]: car.model = user_input[3]
    if len(user_input) > 4 and user_input[4]:
        try:
            car.year = int(user_input[4])
        except ValueError:
            await update.message.reply_text("سنة الصنع يجب أن تكون رقمًا. لم يتم تحديث هذا الحقل.")
    if len(user_input) > 5: car.image_path = user_input[5] or car.image_path

    try:
        session.commit()
        await update.message.reply_text("تم تعديل السيارة بنجاح!")
    except Exception as e:
        session.rollback()
        await update.message.reply_text(f"حدث خطأ أثناء التعديل: {str(e)}")
    finally:
        session.close()
        context.user_data.pop('car_id', None)

    await update.message.reply_text("اختر إجراء آخر:", reply_markup=create_admin_keyboard())
    return CHOOSE_ACTION

async def delete_car(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """حذف سيارة من قاعدة البيانات"""
    user_id = update.message.from_user.id
    if not is_admin(user_id):
        await update.message.reply_text("عذرًا، هذا الأمر مخصص للأدمن فقط.")
        return ConversationHandler.END

    query = update.message.text
    session = Session()
    car = session.query(Car).filter(
        (Car.chassis_number == query) | (Car.plate_number == query)
    ).first()
    if car:
        try:
            session.delete(car)
            session.commit()
            await update.message.reply_text("تم حذف السيارة بنجاح!")
        except Exception as e:
            session.rollback()
            await update.message.reply_text(f"حدث خطأ أثناء الحذف: {str(e)}")
    else:
        await update.message.reply_text("لم يتم العثور على السيارة.")
    session.close()

    await update.message.reply_text("اختر إجراء آخر:", reply_markup=create_admin_keyboard())
    return CHOOSE_ACTION

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """إلغاء العملية الحالية والعودة إلى القائمة الرئيسية"""
    await update.message.reply_text("تم إلغاء العملية.")
    await update.message.reply_text("اختر إجراء:", reply_markup=create_admin_keyboard())
    return CHOOSE_ACTION

# إنشاء محادثة المسؤول
admin_conv_handler = ConversationHandler(
    entry_points=[CommandHandler('admin', admin_panel)],
    states={
        CHOOSE_ACTION: [CallbackQueryHandler(admin_callback)],
        ADD_CAR: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_car)],
        EDIT_CAR_SEARCH: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_car_search)],
        EDIT_CAR: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_car)],
        DELETE_CAR: [MessageHandler(filters.TEXT & ~filters.COMMAND, delete_car)],
    },
    fallbacks=[CommandHandler('cancel', cancel)]
)

# يمكنك إضافة هذا المعالج إلى التطبيق الخاص بك
# application.add_handler(admin_conv_handler)
