from enum import Enum

class Frequency(Enum):
    DAILY, WEEKLY, MONTHLY, YEARLY = range(4)

class Home:
    def __init__(self, name: str):
        self.name = name
        self.rooms = []
        self.members = []
        self.lists = {}
        self.rotations = {}
        self.chat_id = None
    
    def is_member(self, displayname: str):
        for member in self.members:
            if member.displayname == displayname:
                return True
        
        return False
    
    def is_room(self, name: str):
        for room in self.rooms:
            if room.name == name:
                return True
        
        return False
    
    def is_list(self, name: str):
        return name in self.lists.keys()
    
    def is_rotation(self, name: str):
        return name in self.rotations.keys()
    
    def __str__(self):
        return self.name

class Room:
    def __init__(self, name: str):
        self.name = name
    
    def __str__(self):
        return self.name

class Member:
    def __init__(self, displayname: str):
        self.displayname = displayname
    
    def __str__(self):
        return self.displayname

class List:
    def __init__(self, name: str):
        self.name = name
        self.content = []
    
    def __str__(self):
        return self.name + ": " + " ".join(self.content)

class Rotation:
    def __init__(self, name: str):
        self._home = None
        self.name = name
        self.rooms = []
        self.members = []
        self.frequency = None
        self.offset = 0
        self.completed = []
    
    def __str__(self):
        return "--Rooms: " + " ".join(self.rooms) + "\n--Members: " + " ".join(self.members) + "\n--Frequency: " + self.frequency