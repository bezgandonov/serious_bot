from aiogram import Dispatcher, Bot, executor, types
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher import FSMContext
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from config.tokens import BOT_API
from config import messages
from db_helper import create_tables, is_admin_check, get_basic_templates, get_template_cards, delete_template
from db_helper import add_template as add_template_to_db
from db_helper import edit_template as edit_template_in_db
from request_helper import get_all

create_tables()
messages.create_messages()

bot = Bot(token = BOT_API)
dp = Dispatcher(bot, storage=MemoryStorage())


@dp.message_handler(commands=['start'], state='*')
async def start_message(message: types.Message, state: FSMContext):
    await state.finish()
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(text='Перейти в меню', callback_data='return_to_start'))
    with open('start_image.jpg', 'rb') as file:
        await bot.send_photo(message.chat.id, photo=file, caption=messages.get_text('START'), reply_markup=markup)


@dp.callback_query_handler(lambda query: query.data == 'info')
async def show_info(callback_query: types.CallbackQuery):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(text='Вернуться в меню', callback_data='return_to_start'))
    await bot.send_message(callback_query.from_user.id, text=messages.get_text('INFO'), reply_markup=markup)
    await bot.delete_message(chat_id=callback_query.message.chat.id, message_id=callback_query.message.message_id)


class Form(StatesGroup):
    searching = State()


@dp.callback_query_handler(lambda query: query.data == 'search')
async def get_search_query(callback_query: types.CallbackQuery, state: FSMContext):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(text='Вернуться в меню', callback_data='return_to_start'))
    await bot.send_message(callback_query.from_user.id, 'Введите интересующий вас ИНН:', reply_markup=markup)
    await bot.delete_message(chat_id=callback_query.message.chat.id, message_id=callback_query.message.message_id)
    await Form.searching.set()


@dp.message_handler(state=Form.searching)
async def process_search_query(message: types.Message, state: FSMContext):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(text='Вернуться в меню', callback_data='return_to_start:dont'))

    message_to_send = get_all(message.text)

    await bot.send_message(message.chat.id, str(message_to_send), reply_markup=markup, parse_mode=types.ParseMode.HTML)
    await Form.searching.set()

@dp.callback_query_handler(lambda query: query.data == 'request_consult')
async def request_consult(callback_query: types.CallbackQuery):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(text='Вернуться в меню', callback_data='return_to_start'))

    await bot.send_message(callback_query.message.chat.id, 'Тут пока-что ничего нет', reply_markup=markup)
    await bot.delete_message(chat_id=callback_query.message.chat.id, message_id=callback_query.message.message_id)


@dp.callback_query_handler(lambda query: query.data.startswith('return_to_start'), state='*')
async def return_to_start(callback_query: types.CallbackQuery, state: FSMContext):
    markup = start_markup(callback_query.from_user.id)

    with open('menu_image.jpg', 'rb') as file:
        await bot.send_photo(callback_query.from_user.id, photo=file, caption=messages.get_text('MENU'), reply_markup=markup)
    await state.finish()
    if callback_query.data.split(':')[-1] != 'dont':
        await bot.delete_message(chat_id=callback_query.message.chat.id, message_id=callback_query.message.message_id)


@dp.callback_query_handler(lambda query: query.data == 'choose_template' or query.data == 'remove_template' or query.data == 'edit_template')
async def template_shenanigans(callback_query: types.CallbackQuery, page_number: int = 1, is_first: bool = True):
    basic_templates = get_basic_templates()
   
    if basic_templates:
        num_templates = len(basic_templates)
        num_pages = (num_templates + 4) // 5

        start_index = (page_number - 1) * 5
        end_index = min(start_index + 5, num_templates)
        current_templates = basic_templates[start_index:end_index]

        markup = types.InlineKeyboardMarkup()
        message_text = ''
        button_list = []
        count = 0
        for i in current_templates:
            count += 1
            id, name, price, desc = i
            message_text+=f'<b>{count}: {name}</b>\n{price} рублей\n{desc}\n'
            if is_first: 
                button_list.append(types.InlineKeyboardButton(text=f'{count}', callback_data=f'{callback_query.data}_fr:{id}:{page_number}'))
            else:
                button_list.append(types.InlineKeyboardButton(text=f'{count}', callback_data=f'{callback_query.data.split(":")[-1]}:{id}:{page_number}'))

        for i in button_list:
            markup.add(i)

        if num_pages > 1:
            if page_number < num_pages:
                markup.add(types.InlineKeyboardButton(text="След", callback_data=f"change_page:{page_number + 1}"))
            if page_number > 1:
                markup.add(types.InlineKeyboardButton(text="Пред", callback_data=f"change_page:{page_number - 1}"))

        markup.add(types.InlineKeyboardButton(text='Вернуться в меню', callback_data='return_to_start'))

        await bot.send_message(callback_query.from_user.id, message_text, reply_markup=markup, parse_mode=types.ParseMode.HTML)
    else:
        markup2 = types.InlineKeyboardMarkup()
        markup2.add(types.InlineKeyboardButton(text='Вернуться в меню', callback_data='return_to_start'))
        await bot.send_message(callback_query.from_user.id, 'Не удалось найти ни одного шаблона', reply_markup=markup2)
    await bot.delete_message(chat_id=callback_query.message.chat.id, message_id=callback_query.message.message_id)


@dp.callback_query_handler(lambda query: query.data.startswith('choose_template_fr'))
async def choose_template_fr(callback_query: types.CallbackQuery):
    splited_callback = callback_query.data.split(':')
    template_info = get_template_cards(int(splited_callback[1]))

    if template_info:
        name, price, desc, image_path, _ = template_info[0]

        markup = types.InlineKeyboardMarkup()
        buy_button = types.InlineKeyboardButton(text=f'Купить шаблон за {price} рублей', callback_data=f'buy_template:{splited_callback[1]}')
        return_button = types.InlineKeyboardButton(text='Вернуться назад', callback_data=f'change_page:{splited_callback[2]}:{splited_callback[0]}')

        markup.add(buy_button)
        markup.add(return_button)

        message_text = f'<b>Name:</b> {name}\n<b>Price:</b> {price} рублей\n<b>Description:</b> {desc}'
        with open(image_path, 'rb') as file:
            await bot.send_photo(callback_query.from_user.id, photo=file, caption=message_text, reply_markup=markup, parse_mode=types.ParseMode.HTML)
    else:
        await bot.send_message(callback_query.from_user.id, 'Не найдено')
    await bot.delete_message(chat_id = callback_query.message.chat.id, message_id=callback_query.message.message_id)


@dp.callback_query_handler(lambda query: query.data.startswith('change_page'))
async def change_page(callback_query: types.CallbackQuery):
    splited_callback = callback_query.data.split(':')
    await template_shenanigans(callback_query, int(splited_callback[1]), False)


class AddTemplate(StatesGroup):
    Name = State()
    Price = State()
    Description = State()
    Image = State()
    File = State()

class ChangeTemplate(StatesGroup):
    Template_changed_item = State()


@dp.message_handler(commands=['cancel'],state=[AddTemplate.Name,AddTemplate.Price,AddTemplate.Description,AddTemplate.Image,AddTemplate.File,ChangeTemplate.Template_changed_item])
async def cancel_operation(message: types.Message, state: FSMContext):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(text='Вернуться в меню', callback_data='return_to_start'))
    await state.finish()
    await bot.send_message(message.from_user.id, 'Операция была отменена',reply_markup=markup)


@dp.callback_query_handler(lambda query: query.data == 'bot_edit')
async def bot_edit(callback_query: types.CallbackQuery):
    markup = types.InlineKeyboardMarkup()
    add_template_button = types.InlineKeyboardButton(text='Добавить шаблон', callback_data='add_template')
    remove_template_button = types.InlineKeyboardButton(text='Удалить шаблон', callback_data='remove_template')
    edit_templates_button = types.InlineKeyboardButton(text='Изменить уже существующий шаблон', callback_data='edit_template')
    edit_images_button = types.InlineKeyboardButton(text='Изменить картинки в сообщениях', callback_data='edit_images')
    edit_messages_button = types.InlineKeyboardButton(text='Изменить текст в сообщениях', callback_data='edit_messages')
    markup.add(add_template_button)
    markup.add(remove_template_button)
    markup.add(edit_templates_button)
    markup.add(edit_images_button)
    markup.add(edit_messages_button)
    markup.add(types.InlineKeyboardButton(text='Вернуться в меню', callback_data='return_to_start'))

    await bot.send_message(callback_query.from_user.id, 'Редактор бота', reply_markup=markup)
    await bot.delete_message(chat_id=callback_query.message.chat.id, message_id=callback_query.message.message_id)


@dp.callback_query_handler(lambda query: query.data.startswith('remove_template_fr'))
async def remove_template_fr(callback_query: types.CallbackQuery):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(text='Вернуться в меню', callback_data='return_to_start'))
    template_id = int(callback_query.data.split(':')[1])
    success, error_msg = delete_template(template_id)

    if success:
        await bot.send_message(callback_query.from_user.id, f'Шаблон с id {template_id} был упешно удалён',reply_markup=markup)
    else:
        await bot.send_message(callback_query.from_user.id, f'Произошла ошибка при удалении шаблона: {error_msg}',reply_markup=markup)
    await bot.delete_message(chat_id = callback_query.message.chat.id, message_id=callback_query.message.message_id)


@dp.callback_query_handler(lambda query: query.data.startswith('edit_template_fr'))
async def edit_template_fr(callback_query: types.CallbackQuery):
    template_id = int(callback_query.data.split(':')[1])
    template_row_items = [('name', 'название'),
                          ('price', 'цена'),
                          ('desc', 'описание'),
                          ('image_path', 'картинка'),
                          ('file_path', 'шаблон')]

    markup = types.InlineKeyboardMarkup()
    for i in template_row_items:
        markup.add(types.InlineKeyboardButton(text=i[1], callback_data=f'change_template:{i[0]}:{template_id}'))
    markup.add(types.InlineKeyboardButton(text='Вернуться в меню', callback_data='return_to_start'))
    await bot.send_message(callback_query.message.chat.id, 'Что именно вы хотите изменить?', reply_markup=markup)
    await bot.delete_message(chat_id = callback_query.message.chat.id, message_id=callback_query.message.message_id)


@dp.callback_query_handler(lambda query: query.data.startswith('change_template'))
async def template_item_ready(callback_query: types.CallbackQuery, state: FSMContext):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(text='Отмена', callback_data='return_to_start'))
    await bot.send_message(callback_query.message.chat.id, 'Пришлите замену', reply_markup=markup)
    await ChangeTemplate.Template_changed_item.set()
    async with state.proxy() as data:
        splitted_data = callback_query.data.split(':')
        data['item_name'] = splitted_data[1]
        data['template_id'] = splitted_data[2]
    await bot.delete_message(chat_id = callback_query.message.chat.id, message_id=callback_query.message.message_id)


@dp.message_handler(content_types=['text','photo','document'], state = ChangeTemplate.Template_changed_item)
async def change_template(message: types.Message, state: FSMContext):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(text='Вернуться в меню', callback_data='return_to_start'))
    changed_item = message.text
    async with state.proxy() as data:
        if data['item_name'] == 'image_path':
            if message.content_type != types.ContentType.PHOTO:
                await bot.send_message(message.chat.id, 'Вы прислали не картинку, попробуйте снова')
                return
            else:
                changed_item = f'images/{data["template_id"]}.jpg'
        elif data['item_name'] == 'file_path':
            if message.content_type != types.ContentType.DOCUMENT:
                await bot.send_message(message.chat.id, 'Вы прислали не документ, попробуйте снова')
                return
            else:
                changed_item = f'files/{data["template_id"]}.docx'
        elif data['item_name'] == 'price' and not message.text.isdigit():
            await bot.send_message(message.chat.id, 'Вы прислали не цифру, попробуйте снова')
            return

        success, error = edit_template_in_db(data['item_name'], data['template_id'], changed_item)
        await state.finish()
        if success:
            if message.content_type == types.ContentType.PHOTO:
                file_path = await bot.get_file(message.photo[-1].file_id)
                await file_path.download(destination_file=changed_item)
            elif message.content_type == types.ContentType.DOCUMENT:
                file_path = await bot.get_file(message.document[-1].file_id)
                await file_path.download(destination_file=changed_item)
            await bot.send_message(message.chat.id, 'Замена прошла успешно', reply_markup=markup)
        else:
            await bot.send_message(message.chat.id, f'Замена не прошла успешно: {error}', reply_markup=markup)
        await bot.delete_message(chat_id = message.chat.id, message_id=message.message_id-1)
        await bot.delete_message(chat_id = message.chat.id, message_id=message.message_id)


@dp.callback_query_handler(lambda query: query.data == 'add_template')
async def add_template(callback_query: types.CallbackQuery):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(text='Отмена', callback_data='return_to_start'))
    await bot.send_message(callback_query.from_user.id, 'Введите название нового шаблона:', reply_markup=markup)
    await bot.delete_message(chat_id = callback_query.message.chat.id, message_id=callback_query.message.message_id)
    await AddTemplate.Name.set()


@dp.callback_query_handler(lambda query: query.data == 'edit_images', state='*')
async def edit_images(callback_query: types.CallbackQuery, state: FSMContext):
    await state.finish()
    markup = types.InlineKeyboardMarkup()
    change_start_image = types.InlineKeyboardButton(text='Стартового сообщения', callback_data='change_image:start_image.jpg')
    change_menu_image = types.InlineKeyboardButton(text='Меню', callback_data='change_image:menu_image.jpg')
    markup.add(change_start_image)
    markup.add(change_menu_image)
    markup.add(types.InlineKeyboardButton(text='Вернуться в меню', callback_data='return_to_start'))
    await bot.send_message(callback_query.message.chat.id, 'Изменить картинку...', reply_markup=markup)
    await bot.delete_message(chat_id = callback_query.message.chat.id, message_id=callback_query.message.message_id)

class EditMessages(StatesGroup):
    EditImage = State()
    EditText = State()

@dp.callback_query_handler(lambda query: query.data.startswith('change_image'))
async def change_image(callback_query: types.CallbackQuery, state: FSMContext):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(text='Нет', callback_data='return_to_start'))
    file_name = callback_query.data.split(':')[1]
    with open(file_name, 'rb') as file:
        await bot.send_photo(callback_query.message.chat.id, file, caption='Вы уверены что хотите поменять эту картинку?\nЕсли да, то пришлите замену', reply_markup=markup)
    await bot.delete_message(chat_id = callback_query.message.chat.id, message_id=callback_query.message.message_id)
    await EditMessages.EditImage.set()
    await state.update_data(file_name=file_name)

@dp.message_handler(content_types=['photo'], state=EditMessages.EditImage)
async def save_image(message: types.Message, state: FSMContext):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(text='Вернуться в меню', callback_data='return_to_start'))
    try:
        file_id = message.photo[-1].file_id
        file_path = await bot.get_file(file_id)
        state_data = await state.get_data()
        file_name = state_data.get('file_name')
        await file_path.download(destination_file=file_name)
        await bot.send_message(message.chat.id, 'Картинка успешно была изменена', reply_markup=markup)
        await state.finish()
    except:
        await bot.send_message(message.chat.id, 'Что-то пошло не так, попробуйте снова', reply_markup=markup)

@dp.callback_query_handler(lambda query: query.data == 'edit_messages', state='*')
async def edit_messages(callback_query: types.CallbackQuery, state: FSMContext):
    markup = types.InlineKeyboardMarkup()
    start_message_button = types.InlineKeyboardButton(text = 'Приветственного', callback_data='change_message:START')
    menu_message_button = types.InlineKeyboardButton(text = 'Меню', callback_data='change_message:MENU')
    info_message_button = types.InlineKeyboardButton(text = 'Информационного', callback_data='change_message:INFO')
    markup.add(start_message_button)
    markup.add(menu_message_button)
    markup.add(info_message_button)
    markup.add(types.InlineKeyboardButton(text='Вернуться в меню', callback_data='return_to_start'))
    await bot.send_message(callback_query.message.chat.id, 'Текст какого сообщения вы хотите изменить?', reply_markup=markup)
    await bot.delete_message(chat_id = callback_query.message.chat.id, message_id=callback_query.message.message_id)

@dp.callback_query_handler(lambda query: query.data.startswith('change_message'))
async def change_message(callback_query: types.CallbackQuery, state: FSMContext):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(text='Нет', callback_data='return_to_start'))
    await bot.send_message(callback_query.message.chat.id, 'Вы уверены что хотите поменять текст сообщения?\nЕсли да, то пришлите замену', reply_markup=markup)
    message_name = callback_query.data.split(':')[1]
    await EditMessages.EditText.set()
    await state.update_data(message_name=message_name)
    await bot.delete_message(chat_id = callback_query.message.chat.id, message_id=callback_query.message.message_id)

@dp.message_handler(content_types='any', state=EditMessages.EditText)
async def save_message(message: types.Message, state: FSMContext):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(text='Нет', callback_data='return_to_start'))
    try:
        state_data = await state.get_data()
        message_name = state_data.get('message_name')
        messages.change_text(message_name, message.text)
        await bot.send_message(message.chat.id, 'Текст сообщения успешно был изменён', reply_markup=markup)
        await state.finish()
    except:
        await bot.send_message(message.chat.id, 'Что-то пошло не так, попробуйте снова', reply_markup=markup)


@dp.message_handler(content_types='any', state=AddTemplate.Name)
async def process_name(message: types.Message, state: FSMContext):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(text='Отмена', callback_data='return_to_start'))
    if message.content_type != types.ContentType.TEXT:
        await bot.send_message(message.chat.id, 'Вы прислали не текст, поробуйте снова', reply_markup=markup)
        await AddTemplate.Name.set()
        return
    
    async with state.proxy() as data:
        data['name'] = message.text
    await message.answer('Введите цену нового шаблона в рублях:', reply_markup=markup)
    await bot.delete_message(chat_id = message.chat.id, message_id=message.message_id-1)
    await bot.delete_message(chat_id = message.chat.id, message_id=message.message_id)
    await AddTemplate.Price.set()


@dp.message_handler(content_types='any', state=AddTemplate.Price)
async def process_price(message: types.Message, state: FSMContext):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(text='Отмена', callback_data='return_to_start'))
    if message.content_type != types.ContentType.TEXT or not message.text.isdigit():
        await bot.send_message(message.chat.id, 'Вы прислали не число, поробуйте снова', reply_markup=markup)
        await AddTemplate.Price.set()
        return

    async with state.proxy() as data:
        data['price'] = message.text
    await message.answer('Введите описание шаблона:', reply_markup=markup)
    await bot.delete_message(chat_id = message.chat.id, message_id=message.message_id-1)
    await bot.delete_message(chat_id = message.chat.id, message_id=message.message_id)
    await AddTemplate.Description.set()


@dp.message_handler(content_types='any', state=AddTemplate.Description)
async def process_description(message: types.Message, state: FSMContext):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(text='Отмена', callback_data='return_to_start'))
    if message.content_type != types.ContentType.TEXT:
        await bot.send_message(message.chat.id, 'Вы прислали не текст, поробуйте снова', reply_markup=markup)
        await AddTemplate.Description.set()
        return

    async with state.proxy() as data:
        data['desc'] = message.text
    await message.answer('Пришлите картинку шаблона:', reply_markup=markup)
    await bot.delete_message(chat_id = message.chat.id, message_id=message.message_id-1)
    await bot.delete_message(chat_id = message.chat.id, message_id=message.message_id)
    await AddTemplate.Image.set()


@dp.message_handler(content_types='any', state=AddTemplate.Image)
async def process_image(message: types.Message, state: FSMContext):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(text='Отмена', callback_data='return_to_start'))
    if message.content_type != types.ContentType.PHOTO:
        await bot.send_message(message.chat.id, 'Вы прислали не картинку, поробуйте снова', reply_markup=markup)
        await AddTemplate.Image.set()
        return

    file_id = message.photo[-1].file_id

    async with state.proxy() as data:
        data['image'] = {}
        data['image']['file_id'] = file_id

    await message.answer('Пришлите сам шаблон (формат .docx):', reply_markup=markup)
    await bot.delete_message(chat_id = message.chat.id, message_id=message.message_id-1)
    await bot.delete_message(chat_id = message.chat.id, message_id=message.message_id)
    await AddTemplate.File.set()


@dp.message_handler(content_types='any', state=AddTemplate.File)
async def process_file(message: types.Message, state: FSMContext):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(text='Отмена', callback_data='return_to_start'))
    if message.content_type != types.ContentType.DOCUMENT:
        await bot.send_message(message.chat.id, 'Вы прислали не документ, поробуйте снова', reply_markup=markup)
        await AddTemplate.Image.set()
        return

    markup2 = types.InlineKeyboardMarkup()
    markup2.add(types.InlineKeyboardButton(text='Вернуться в меню', callback_data='return_to_start'))

    file_id = message.document.file_id

    async with state.proxy() as data:
        data['template'] = {}
        data['template']['file_id'] = file_id

    try:
        async with state.proxy() as data:
            name = data['name']
            price = data['price']
            desc = data['desc']
            image_file_id = data['image']['file_id']
            template_file_id = data['template']['file_id']

            is_success, error_msg, template_id = add_template_to_db(name, price, desc)
            if is_success:
                file_path = await bot.get_file(image_file_id)
                await file_path.download(destination_file=f'images/{template_id}.jpg')
                file_path = await bot.get_file(template_file_id)
                await file_path.download(destination_file=f'files/{template_id}.docx')

                await bot.send_message(message.from_user.id, 'Добавление шаблона прошло успешно', reply_markup=markup2)
            else:
                delete_template(template_id)

                await bot.send_message(message.from_user.id, f'При добавлении шаблона произошла ошибка: {error_msg}', reply_markup=markup2)
    except Exception as e:
        await bot.send_message(message.from_user.id, f'Произошла ошибка при обработке файла: {e}', reply_markup=markup2)
    finally:
        await bot.delete_message(chat_id = message.chat.id, message_id=message.message_id-1)
        await bot.delete_message(chat_id = message.chat.id, message_id=message.message_id)
        await state.finish()
        

def start_markup(user_id):
    is_admin = is_admin_check(user_id)

    markup = types.InlineKeyboardMarkup()
    info_button = types.InlineKeyboardButton(text='информация', callback_data='info')
    search_button = types.InlineKeyboardButton(text='поиск по ИНН', callback_data='search')
    template_button = types.InlineKeyboardButton(text='купить шаблон', callback_data='choose_template')
    admin_button = types.InlineKeyboardButton(text='редактировать бота', callback_data='bot_edit')
    request_consult = types.InlineKeyboardButton(text='заказать консультацию', callback_data='request_consult')

    markup.add(info_button)
    markup.add(search_button)
    markup.add(template_button)
    markup.add(request_consult)
    if is_admin:
        markup.add(admin_button)

    return(markup)


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
