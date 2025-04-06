from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler, ConversationHandler
from user import start, search, request_car, save_request
from admin import admin_panel, admin_callback, add_car, edit_car_search, edit_car, delete_car, cancel, CHOOSE_ACTION, ADD_CAR, EDIT_CAR_SEARCH, EDIT_CAR, DELETE_CAR
from database import populate_initial_data

# توكن البوت (استبدله بتوكن البوت الخاص بك من BotFather)
TOKEN = "#######################"

def main():
    # ملء البيانات الأولية
    populate_initial_data()

    # إعداد البوت
    app = Application.builder().token(TOKEN).build()

    # أوامر الأدمن باستخدام ConversationHandler
    admin_conv_handler = ConversationHandler(
        entry_points=[CommandHandler("admin", admin_panel)],
        states={
            CHOOSE_ACTION: [CallbackQueryHandler(admin_callback)],
            ADD_CAR: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_car)],
            EDIT_CAR_SEARCH: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_car_search)],
            EDIT_CAR: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_car)],
            DELETE_CAR: [MessageHandler(filters.TEXT & ~filters.COMMAND, delete_car)],
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )
    app.add_handler(admin_conv_handler)

    # أوامر المستخدم
    # ConversationHandler لإدارة البحث وطلب الاستلام
    user_conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            0: [MessageHandler(filters.TEXT & ~filters.COMMAND, search)],
            1: [CallbackQueryHandler(request_car, pattern="^request_")],
            2: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_request)],
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )
    app.add_handler(user_conv_handler)

    # أمر /addcar المباشر
    app.add_handler(CommandHandler("addcar", add_car))

    # تشغيل البوت
    app.run_polling()

if __name__ == '__main__':
    main()
