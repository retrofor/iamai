# 存一些类用
import time
import os


class logger:
    # file = './log/' + time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()) + '.txt'
    file = './log/' + time.strftime("%Y-%m-%d-%H-%M-%S", time.localtime()) + '.log'
    log = f'Logged from {time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())}' + '\n'
    level = 'info'

    def __init__(self, file=None, level='info'):
        if not os.path.isdir('../Bot/log'):
            os.mkdir('../Bot/log')
        if file:
            self.file = file
        self.level = level

    def __del__(self):
        f = open(self.file, 'w', encoding='utf-8')
        f.write(self.log)
        f.close()

    def info(self, t):
        self.log = self.log + f'[{time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())}] [INFO]: ' + t + '\n'
        print(f'[{time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())}] [INFO]: ' + t)

    def warn(self, t):
        self.log = self.log + f'[{time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())}] [WARN]: ' + t + '\n'
        print(f'[{time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())}] [INFO]: ' + t)

    def fatal(self, t):
        self.log = self.log + f'[{time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())}] [FATAL]: ' + t + '\n'
        print(f'[{time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())}] [INFO]: ' + t)

    def debug(self, t):
        if self.level == 'info':
            return
        self.log = self.log + f'[{time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())}] [DEBUG]: ' + t + '\n'
        print(f'[{time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())}] [INFO]: ' + t)


class group_info:
    id = 100001
    name = 'Group'
    memo = 'Memo'
    create_time = '1672502400'
    level = '1'
    member_count = '1'
    max_member_count = '200'

    def __init__(self,
                 id=100001,
                 name='Group',
                 memo='Memo',
                 create_time='1672502400',
                 level='1',
                 member_count='1',
                 max_member_count='200'
                 ):
        self.id = id
        self.name = name
        self.memo = memo
        self.create_time = create_time
        self.level = level
        self.member_count = member_count
        self.max_member_count = max_member_count


class friend_info:
    id = 10001
    mame = 'name'
    remark = 'remark'

    def __init__(self,
                 id=10001,
                 name='name',
                 remark='remark'
                 ):
        self.id = id
        self.name = name
        self.remark = remark


class sender:
    id = 10001
    nickname = 'nickname'
    sex = 'unknown'
    age = 105
    card = 'card'
    area = 'China'
    level = '0'
    role = 'member'
    title = 'title'

    def __init__(self,
                 user_id=10001,
                 nickname='nickname',
                 sex='unknown',
                 age=105,
                 card='card',
                 area='China',
                 level='0',
                 role='member',
                 title='title'
                 ):
        self.user_id = user_id
        self.nickname = nickname
        self.sex = sex
        self.age = age
        self.card = card
        self.area = area
        self.level = level
        self.role = role
        self.title = title


class Message:
    send_time = '1672502400'
    self_id = 10001
    group_id = 100001
    message_type = 'private'
    sub_type = 'friend'
    message_id = 1
    user_id = 10001
    message = 'message'
    raw_message = 'message'
    font = 0
    temp_source = 0

    def __init__(self,
                 send_time='1672502400',
                 self_id=10001,
                 group_id=100001,
                 message_type='private',
                 sub_type='friend',
                 message_id=1,
                 user_id=10001,
                 message='message',
                 raw_message='message',
                 font=0,
                 temp_source=0,
                 sender=None,
                 reply=None
                 ):
        self.sender = sender
        self.send_time = send_time
        self.self_id = self_id
        self.group_id = group_id
        self.message_type = message_type
        self.sub_type = sub_type
        self.message_id = message_id
        self.user_id = user_id
        self.message = message
        self.raw_message = raw_message
        self.font = font
        self.temp_source = temp_source
        self._reply = reply

    def reply(self, message):
        if self.message_type == 'private':
            return self._reply(self.user_id, message)
        else:
            return self._reply(self.group_id, message)


class Notice:
    js = {}  # 原始json
    send_time = 1672502400  # 操作时间戳
    group_id = 100001  # 统一来源群ID
    self_id = 10001  # 统一机器人ID
    notice_type = string
