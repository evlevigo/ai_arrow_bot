import logging
from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from db import dp, conn, cursor
from keyboard import get_keyboard
from datetime import datetime
from langchain_community.chat_models.gigachat import GigaChat
from langchain.schema import SystemMessage, HumanMessage
# Настройка логирования
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# Настройка GigaChat
auth = 'NDMxYTRkZjktYjJjYi00MGQyLTk3NDEtNjY2NmUzNzI5ZThlOjQyMDUwN2JjLTJhMmYtNDRmOC1hYTM0LTg0ZDEyMjExYWVkMQ=='
llm = GigaChat(credentials=auth,
               model='GigaChat:latest',
               verify_ssl_certs=False,
               profanity_check=False)


class TrackingState(StatesGroup):
    tracking = State()
@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    await message.answer("Привет! Что вы хотите сделать?", reply_markup=get_keyboard())
@dp.message_handler(text='Начать отслеживание сообщений')
async def start_tracking(message: types.Message, state: FSMContext):
    await TrackingState.tracking.set()
    await message.answer("Отслеживание сообщений начато.")
@dp.message_handler(text='Прекратить отслеживание сообщений', state=TrackingState.tracking)
async def stop_tracking(message: types.Message, state: FSMContext):
    await state.finish()
    await message.answer("Отслеживание сообщений прекращено.")
@dp.message_handler(state=TrackingState.tracking)
async def track_messages(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    chat_id = message.chat.id
    text = message.text
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    cursor.execute('INSERT INTO messages (user_id, chat_id, message, datetime) VALUES (?, ?, ?, ?)',
                   (user_id, chat_id, text, timestamp))
    conn.commit()

    await message.answer("Сообщение сохранено в базе данных.")
class ChatSummaryState(StatesGroup):
    waiting_for_date = State()
@dp.message_handler(text='Перескажи кратко чат')
async def summarize_chat(message: types.Message):
    await ChatSummaryState.waiting_for_date.set()
    await message.answer("Введите дату в формате YYYY-MM-DD")
@dp.message_handler(state=ChatSummaryState.waiting_for_date)
async def get_date(message: types.Message, state: FSMContext):
    date_str = message.text
    try:
        date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        await message.answer("Некорректный формат даты. Попробуйте снова.")
        return

    cursor.execute('SELECT message FROM messages WHERE datetime LIKE ?', (f'{date}%',))
    chat_summary = [row[0] for row in cursor.fetchall()]

    if not chat_summary:
        await message.answer("Сообщений за эту дату не найдено.")
        await state.finish()
        return

    # Объединяем все сообщения в один текст
    chat_summary_text = "\n".join(chat_summary)
    print("chat_summary_text:", chat_summary_text)

    def generate_response(context, input_text):
        messages = [
            SystemMessage(
                content="Ответь на вопрос пользователя. Используй при этом только информацию из контекста. Если в контексте нет информации для ответа, сообщи об этом пользователю."),
            HumanMessage(content=f"Контекст: {context}\nВопрос: {input_text}\nОтвет:")
        ]
        response = llm(messages)
        return response.content
    # Пример использования
    context = chat_summary_text
    input_text = "Кратко расскажи, о чем говорилось в сообщениях.  \
                 В описании используй лёгкие конструкции предложений,  \
                 чтобы было понятно даже десятилетнему ребёнку.  \
                 Используй одно, два или три предложения."
    try:
        response = generate_response(context, input_text)
        print(response)
        await message.answer("Вот резюме чата:\n" + response)
    except Exception as e:
        logging.error(f"Error while calling GigaChat: {e}")
        await message.answer("Произошла ошибка при обращении к GigaChat. Попробуйте позже.")

    await state.finish()

class NoteState(StatesGroup):
    waiting_for_note = State()
    waiting_for_delete_id = State()

async def create_note(message: types.Message, state: FSMContext):
    await NoteState.waiting_for_note.set()
    await message.answer("Введите текст заметки:")

async def save_note(message: types.Message, state: FSMContext):
    note_text = message.text
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    cursor.execute('INSERT INTO notes (note, date_time) VALUES (?, ?)', (note_text, timestamp))
    conn.commit()

    await message.answer("Заметка сохранена.")
    await state.finish()

async def delete_note(message: types.Message, state: FSMContext):
    cursor.execute('SELECT id, note FROM notes')
    notes = cursor.fetchall()

    if not notes:
        await message.answer("Список заметок пуст.")
        return

    notes_list = "\n".join([f"{note[0]}: {note[1]}" for note in notes])
    await message.answer(f"Вот список ваших заметок:\n{notes_list}\n\nВведите ID заметки, которую хотите удалить:")
    await NoteState.waiting_for_delete_id.set()

async def confirm_delete_note(message: types.Message, state: FSMContext):
    note_id = message.text

    try:
        note_id = int(note_id)
    except ValueError:
        await message.answer("Некорректный ID заметки. Пожалуйста, введите числовой ID.")
        return

    cursor.execute('DELETE FROM notes WHERE id = ?', (note_id,))
    conn.commit()

    await message.answer("Заметка удалена.")
    await state.finish()

def register_handlers(dp: Dispatcher):
    dp.register_message_handler(cmd_start, commands=['start'])
    dp.register_message_handler(start_tracking, text='Начать отслеживание сообщений')
    dp.register_message_handler(stop_tracking, text='Прекратить отслеживание сообщений', state=TrackingState.tracking)
    dp.register_message_handler(track_messages, state=TrackingState.tracking)
    dp.register_message_handler(summarize_chat, text='Перескажи кратко чат')
    dp.register_message_handler(get_date, state=ChatSummaryState.waiting_for_date)
    dp.register_message_handler(create_note, text='Создать заметку')
    dp.register_message_handler(save_note, state=NoteState.waiting_for_note)
    dp.register_message_handler(delete_note, text='Удалить заметку')
    dp.register_message_handler(confirm_delete_note, state=NoteState.waiting_for_delete_id)