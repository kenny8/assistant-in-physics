from flask import Flask
from flask import request
import json
import copy
import MySQLdb
import random


def db_seach(txt):  # выдача данных из базы данных
    db = MySQLdb.connect(host="McKenny.mysql.pythonanywhere-services.com",
                         user="McKenny", passwd="qwerty123", db="McKenny$formulas_of_physics", charset='utf8mb4')
    cur = db.cursor()
    result = cur.execute(txt)
    data = cur.fetchall()
    db.close()
    return data


app = Flask(__name__)

physics = {'section': '', "subsection": "", 'name_of_formula': '', 'last_word': '', 'mode': '', 'question': [],
           'last_question': [], 'work': False, 'answer_true_or_false': True}

USERS = {}


@app.route('/post', methods=['POST'])
def main():  # выдача и получение ответыа/вопросав json
    response = {
        'session': request.json['session'],
        'version': request.json['version'],
        'response': {
            'end_session': False
        }
    }
    handle_dialog(response, request.json)
    return json.dumps(response)


def tips(where, what, word, user_id, new=False):
    global USERS
    tips_txt = set()
    if new:
        result = db_seach("""SELECT section FROM section_of_physics """)
    else:
        result = db_seach("""SELECT {} FROM section_of_physics WHERE {} = '{}'""".format(what, where, word))
    for elem in result:
        tips_txt.add(elem[0])
    if where == 'section' and USERS[user_id][0]['mode'] == 'remember':
        txt = 'какой подтип вы хотите? Например'
    elif where == 'section' and USERS[user_id][0]['mode'] == 'study':
        txt = 'вы хотите выучить все формулы из раздела {}, тогда скажите: начнем, или из конкректного подтипа Например'.format(
            word)
    elif where == 'subsection':
        txt = 'какой формулу вы хотите? Например'
    elif where == 'name_of_formula':
        txt = 'какой подтип вы хотите? Например'
    elif new and USERS[user_id][0]['mode'] == 'remember':
        txt = 'Я справочник по физике, Я могу напомнить формулу, подкажите из какого раздела. Например'
    elif new and USERS[user_id][0]['mode'] == 'study':
        txt = 'Я справочник по физике, Я помогу  заучить формулу, подкажите из какого раздела. Например'
    for nof in tips_txt:
        txt += ', ' + nof
    return (txt, tips_txt)


def get_answer(user_id):  # ответ
    if USERS[user_id][0]['subsection'] != '' and USERS[user_id][0]['name_of_formula'] != '':
        result1 = db_seach(
            """SELECT formyla_read FROM section_of_physics WHERE subsection = '{}' and name_of_formula = '{}'""".format(
                USERS[user_id][0]['subsection'], USERS[user_id][0]['name_of_formula']))
        result2 = db_seach(
            """SELECT id_formula FROM section_of_physics WHERE subsection = '{}' and name_of_formula = '{}'""".format(
                USERS[user_id][0]['subsection'], USERS[user_id][0]['name_of_formula']))
        return (result2[0][0], result1[0][0])
    return False


def cheak_answer(word, res, user_id):
    global USERS
    txt = ('возможно вы ошиблись', {})
    section = set()  # тип формулы, например  механика
    subsection = set()  # подтип фолмулы например равномерное движение в механике
    name_of_formula = set()  # название формулы

    result = db_seach(
        """SELECT section, subsection, name_of_formula FROM section_of_physics""")  # получение всех данных из таблицы
    for elem in result:
        section.add(elem[0])
        subsection.add(elem[1])
        name_of_formula.add(elem[2])

    if word == 'повтори':
        txt = (USERS[user_id][0]['last_word'], {'повтори', 'напомни'})
        return txt
    elif word != 'повтори' and get_answer(user_id):
        USERS[user_id][0]['name_of_formula'] = ''
        USERS[user_id][0]['subsection'] = ''

    if word == 'напомни':
        USERS[user_id][0]['section'] = ''
        USERS[user_id][0]['name_of_formula'] = ''
        USERS[user_id][0]['subsection'] = ''
        k = tips('', '', '', user_id, True)
        txt = (k[0][23:], k[1])

    wor = word.split()

    for wod in wor:  # разбор предложения пользователя
        if len(wod) >= 3:
            for sec in section:
                if sec.startswith(wod[:-2]):
                    USERS[user_id][0]['section'] = sec
                    txt = tips('section', 'subsection', sec, user_id)
            for sub in subsection:
                if sub.startswith(wod[:-2]):
                    USERS[user_id][0]['subsection'] = sub
            for n_of_f in name_of_formula:
                if n_of_f.startswith(wod[:-2]):
                    USERS[user_id][0]['name_of_formula'] = n_of_f

    if USERS[user_id][0]['name_of_formula'] == '' and USERS[user_id][0]['subsection'] != '':   # следущийй  вопрос
        txt = tips('subsection', 'name_of_formula', USERS[user_id][0]['subsection'], user_id)  # взависимости  от  
    elif USERS[user_id][0]['subsection'] == '' and USERS[user_id][0]['name_of_formula'] != '':  # того что известно
        txt = tips('name_of_formula', 'subsection', USERS[user_id][0]['name_of_formula'], user_id)
    USERS[user_id][0]['last_word'] = txt[0]
    return txt


def new_mode(user_id, word):  # меняет режим работы программы
    global USERS
    wor = word.split()
    success = False
    for wod in wor:
        if 'выучить' == wod:
            USERS[user_id][0]['mode'] = 'study'
            success = True
        if 'напомни' == wod:
            USERS[user_id][0]['mode'] = 'remember'
            success = True
    if USERS[user_id][0]['mode'] != '':
        success = True
    return success


def get_answer_study(user_id):  # ответ
    if USERS[user_id][0]['subsection'] != '' and USERS[user_id][0]['name_of_formula'] != '':
        result1 = db_seach(
            """SELECT formyla_read FROM section_of_physics WHERE subsection = '{}' and name_of_formula = '{}'""".format(
                USERS[user_id][0]['subsection'], USERS[user_id][0]['name_of_formula']))
        result2 = db_seach(
            """SELECT id_formula FROM section_of_physics WHERE subsection = '{}' and name_of_formula = '{}'""".format(
                USERS[user_id][0]['subsection'], USERS[user_id][0]['name_of_formula']))
        return (result2[0][0], result1[0][0])
    return False


def answer_study(word, res, user_id):  # раздел  обучения
    txt = ('возможно вы ошиблись', {})
    section = []  # тип формулы, например  механика
    subsection = []  # подтип фолмулы например равномерное движение в механике
    name_of_formula = []  # название формулы
    formyla_read = []  # название формулы

    result = db_seach(
        """SELECT section, subsection, name_of_formula, formyla_read FROM section_of_physics""")  # получение всех данных из таблицы
    for elem in result:
        section.append(elem[0])
        subsection.append(elem[1])
        name_of_formula.append(elem[2])
        formyla_read.append(elem[3])

    if word == 'повтори':
        txt = (USERS[user_id][0]['last_word'], {'повтори', 'напомни'})
        return txt
    elif word != 'повтори' and get_answer(user_id):
        USERS[user_id][0]['name_of_formula'] = ''
        USERS[user_id][0]['subsection'] = ''

    if word == 'стоп':
        txt = ('я могу напомнить формолу и помочь её выучить', {'повтори', 'напомни', 'выучить'})
        return txt

    if word == 'выучить':
        USERS[user_id][0]['section'] = ''
        USERS[user_id][0]['name_of_formula'] = ''
        USERS[user_id][0]['subsection'] = ''
        USERS[user_id][0]['question'].clear()
        k = tips('', '', '', user_id, True)
        txt = (k[0][23:], k[1])
        USERS[user_id][0]['work'] = False

    if word == 'начнем' and USERS[user_id][0]['section'] != '':
        txt = ('все готово, начнем,когда надоест  скажите  стоп', {'стоп'})
        USERS[user_id][0]['subsection'] = '-'
    wor = word.split()
    for wod in wor:  # разбор предложения пользователя
        if len(wod) >= 3:
            for sec in section:
                if sec.startswith(wod[
                                  :-2]):  # если слово находится в саммой верхей части иерархии формул, для ответа неучитывается
                    txt = tips('section', 'subsection', sec, user_id)
                    txt[1].add('начнем')
                    USERS[user_id][0]['section'] = sec
            for sub in subsection:
                if sub.startswith(wod[:-2]):
                    txt = ('все готово, начнем,когда надоест  скажите  стоп', {'стоп'})
                    USERS[user_id][0]['subsection'] = sub

    if USERS[user_id][0]['subsection'] != '' and USERS[user_id][0]['work'] is False:  # составления вопроса
        USERS[user_id][0]['work'] = True
        if USERS[user_id][0]['subsection'] == '-':
            question_work_piece = db_seach(
                """SELECT {}, {}, {}, {} FROM section_of_physics WHERE {} = '{}'""".format('subsection',
                                                                                           'name_of_formula',
                                                                                           'formyla_read', 'id_formula',
                                                                                           'section',
                                                                                           USERS[user_id][0][
                                                                                               'section']))
            for elem in question_work_piece:
                USERS[user_id][0]['question'].append(
                    ['Что за формула {} в разделе {}'.format(elem[1], elem[0]), elem[2], elem[3]])
        else:
            question_work_piece = db_seach(
                """SELECT {}, {}, {} FROM section_of_physics WHERE {} = '{}'""".format('name_of_formula',
                                                                                       'formyla_read', 'id_formula',
                                                                                       'subsection',
                                                                                       USERS[user_id][0]['subsection']))
            for elem in question_work_piece:
                USERS[user_id][0]['question'].append(
                    ['Что за формула {} в разделе {}'.format(elem[0], USERS[user_id][0]['subsection']), elem[1],
                     elem[2]])

    if word == 'следущее':
        USERS[user_id][0]['answer_true_or_false'] = True
        USERS[user_id][0]['last_question'].clear()

    if len(USERS[user_id][0]['last_question']) != 0:  # проверка ответа пользователя
        if word == USERS[user_id][0]['last_question'][0][1]:
            n = USERS[user_id][0]['question'].pop(
                USERS[user_id][0]['question'].index(USERS[user_id][0]['last_question'][0]))
            USERS[user_id][0]['last_question'].clear()
        else:
            txt = ('неправильно', {'стоп', 'следущее'})
            USERS[user_id][0]['answer_true_or_false'] = False

    if len(USERS[user_id][0]['question']) > 0 and USERS[user_id][0]['answer_true_or_false']:  # выбор  нового вопроса
        USERS[user_id][0]['last_question'].append(random.choice(USERS[user_id][0]['question']))
        txt = (USERS[user_id][0]['last_question'][0][0], {'стоп'})
    elif len(USERS[user_id][0]['question']) == 0 and USERS[user_id][0]['subsection'] != '':
        k = tips('', '', '', user_id, True)
        txt = ('тесты по этим формулам закончелись ' + k[0][23:], k[1])
        USERS[user_id][0]['section'] = ''
        USERS[user_id][0]['name_of_formula'] = ''
        USERS[user_id][0]['subsection'] = ''
        USERS[user_id][0]['question'].clear()
        k = tips('', '', '', user_id, True)
        txt = (k[0][23:], k[1])
        USERS[user_id][0]['work'] = False

    USERS[user_id][0]['last_word'] = txt[0]
    return txt


def handle_dialog(res, req):  # выдача ответов
    global USERS
    user_id = req['session']['user_id']
    if req['session']['new']:  # первый раз начала диолога
        titl = set()
        USERS[user_id] = [copy.deepcopy(physics)]  # если новый пользователь, то запоминаем его id
        res['response'][
            'text'] = 'Приветсвую тебя пользователь, я помошник по физике, я могу напомнить формолу и помочь её выучить'  # приветстввенный ответ
        titl.add('повтори')
        titl.add('напомни')
        titl.add('выучить')
        res['response']['buttons'] = [
            {
                'title': tit.title(),
                'hide': True
            } for tit in titl
        ]
    else:
        word = req['request']['command']  # ответ пользователя
        word = word.lower()
        if new_mode(user_id, word):
            if USERS[user_id][0]['mode'] == 'remember':  # найти формолу
                answer = cheak_answer(word, res, user_id)
                if answer[0] != 'возможно вы ошиблись':
                    res['response']['text'] = answer[0]
                    answer[1].add('повтори')
                    answer[1].add('напомни')
                    answer[1].add('выучить')
                    res['response']['buttons'] = [
                        {
                            'title': ans.title(),
                            'hide': True
                        } for ans in answer[1]
                    ]
                elif get_answer(user_id):  # ответ
                    img, title = get_answer(user_id)
                    res['response']['text'] = title + '. Чтобы продолжить скажите: напомни'
                    res['response']['card'] = {
                        "type": "BigImage",
                        "image_id": img,
                        "title": title
                    }
                    word_ans = ['повтори', 'напомни', 'выучить']
                    res['response']['buttons'] = [
                        {
                            'title': wor.title(),
                            'hide': True
                        } for wor in word_ans
                    ]
                else:
                    res['response']['text'] = 'возможно вы ошиблись'
                    word_ans = ['повтори', 'напомни', 'выучить']
                    res['response']['buttons'] = [
                        {
                            'title': wor.title(),
                            'hide': True
                        } for wor in word_ans
                    ]
            elif USERS[user_id][0]['mode'] == 'study':   # выучить  формулу
                answer = answer_study(word, res, user_id)
                if answer[0] != 'возможно вы ошиблись' and answer[0] != 'неправильно':
                    res['response']['text'] = answer[0]
                    answer[1].add('повтори')
                    answer[1].add('напомни')
                    answer[1].add('выучить')
                    res['response']['buttons'] = [
                        {
                            'title': ans.title(),
                            'hide': True
                        } for ans in answer[1]
                    ]
                elif answer[0] == 'неправильно':
                    img = USERS[user_id][0]['last_question'][0][2]
                    title = USERS[user_id][0]['last_question'][0][1]
                    res['response']['text'] = title + '. Чтобы продолжить скажите: следущее'
                    res['response']['card'] = {
                        "type": "BigImage",
                        "image_id": img,
                        "title": title
                    }
                    word_ans = ['повтори', 'напомни', 'выучить', 'следущее']
                    res['response']['buttons'] = [
                        {
                            'title': wor.title(),
                            'hide': True
                        } for wor in word_ans
                    ]
                else:
                    res['response']['text'] = 'возможно вы ошиблись'
                    word_ans = ['повтори', 'напомни', 'выучить']
                    res['response']['buttons'] = [
                        {
                            'title': wor.title(),
                            'hide': True
                        } for wor in word_ans
                    ]
        else:
            res['response']['text'] = 'возможно вы ошиблись'
            word_ans = ['повтори', 'напомни', 'выучить']
            res['response']['buttons'] = [
                {
                    'title': wor.title(),
                    'hide': True
                } for wor in word_ans
            ]
