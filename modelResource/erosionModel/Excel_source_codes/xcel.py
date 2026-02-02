import math
import re
from xml.dom.minidom import parse

def floatv(v):
    if v == None:
        return 0
    if v == "":
        return 0
    return float(v)

class xlvalue:
    def __init__(self, v = 0.0) -> None:
        self.v = v
        return self
    
    def __add__(self, other):
        """重载加法运算符 +"""
        if isinstance(other, xlvalue):
            return xlvalue(self.v + other.v)
        return xlvalue(self.v + other)

    def __sub__(self, other):
        """重载减法运算符 -"""
        if isinstance(other, xlvalue):
            return xlvalue(self.v - other.v)
        return xlvalue(self.v - other)

    def __mul__(self, other):
        """重载乘法运算符 *"""
        if isinstance(other, xlvalue):
            return xlvalue(self.v * other.v)
        return xlvalue(self.v * other)

    def __truediv__(self, other):
        """重载除法运算符 /"""
        if isinstance(other, xlvalue):
            if other.v == 0:
                return 0
            return xlvalue(self.v / other.v)
        if other == 0:
            return 0
        return xlvalue(self.v / other)

    def __eq__(self, other):
        """重载相等运算符 =="""
        if isinstance(other, xlvalue):
            return self.v == other.v
        return self.v == other

    def __ne__(self, other):
        """重载不等运算符 !="""
        if isinstance(other, xlvalue):
            return self.v == other.v
        return self.v == other

    def __lt__(self, other):
        """重载小于运算符 <"""
        if isinstance(other, xlvalue):
            return self.v < other.v
        return self.v < other

    def __le__(self, other):
        """重载小于等于运算符 <="""
        if isinstance(other, xlvalue):
            return self.v <= other.v
        return self.v <= other

    def __gt__(self, other):
        """重载大于运算符 >"""
        if isinstance(other, xlvalue):
            return self.v > other.v
        return self.v > other

    def __ge__(self, other):
        """重载大于等于运算符 >="""
        if isinstance(other, xlvalue):
            return self.v >= other.v
        return self.v >= other
    
    def __mod__(self, other):
        """重载求余运算符 %"""
        if isinstance(other, xlvalue):
            return self.v % other.v
        return self.v % other
    
    def __pow__(self, other):
        """重载次方运算符 **"""
        if isinstance(other, xlvalue):
            return self.v ** other.v
        return self.v ** other

def excel_column_to_number(col):
    """Convert Excel column letter to number. E.g., 'A' -> 1, 'Z' -> 26, 'AA' -> 27."""
    num = 0
    for c in col:
        num = num * 26 + (ord(c.upper()) - ord('A') + 1)
    return num

def number_to_excel_column(num):
    """Convert number to Excel column letter. E.g., 1 -> 'A', 27 -> 'AA'."""
    col = ""
    while num > 0:
        num, remainder = divmod(num - 1, 26)
        col = chr(65 + remainder) + col
    return col
import re

def cell_to_row_col(cell):
    # 使用正则表达式分割字母和数字部分
    match = re.match(r"([A-Z]+)(\d+)", cell, re.I)
    if match:
        items = match.groups()
        col = items[0]
        row = int(items[1])
        
        # 将列字母转换为列号
        col_num = 0
        for char in col:
            col_num = col_num * 26 + (ord(char.upper()) - ord('A')) + 1
        
        return (row, col_num)
    else:
        raise ValueError(f"Invalid cell format: {cell}")

def row_col_to_cell(row, col):
    # 将列号转换为列字母
    col_str = ""
    while col > 0:
        col -= 1
        col_str = chr(col % 26 + ord('A')) + col_str
        col //= 26
    
    return f"{col_str}{row}"

def parse_range(range_str):
    """Parse an Excel range string and return all cell addresses within the range."""
    range_regex = re.compile(r"\$?([A-Za-z]+)\$?(\d+):\$?([A-Za-z]+)\$?(\d+)")
    match = range_regex.match(range_str)
    if not match:
        raise ValueError("Invalid range format")

    start_col, start_row, end_col, end_row = match.groups()
    start_col_num = excel_column_to_number(start_col)
    end_col_num = excel_column_to_number(end_col)
    start_row_num = int(start_row)
    end_row_num = int(end_row)

    cells = []
    for col in range(start_col_num, end_col_num + 1):
        for row in range(start_row_num, end_row_num + 1):
            cell = f"{number_to_excel_column(col)}{row}"
            cells.append(cell)

    return cells

def isnumber(a):
    return isinstance(a, (int, float)) or (isinstance(a, str) and a.isdigit())

class xRange:
    def __init__(self,sheet,name):
        self.name = name
        self.sheet = sheet
        cells = parse_range(name)
        self.cells = [sheet.cell(c) for c in cells]
        for c in self.cells:
            c.rdeps.add(self)
        self.rdeps=set()
    
    @property    
    def value(self):
        values = [c.value for c in self.cells]
        return values
    
    def update_rdeps(self):
        pass

    def rreset(self,cell):
        for c in self.rdeps:
            c.rreset(cell)
    
    def isDep(self,c):
        return c in self.cells
    
class xCell:
    def __init__(self,sheet,name,v=None,f=None):
        self.name = name
        self.sheet = sheet
        self.v = v
        self.f = f
        self.text = ""
        self.deps=None
        self.rdeps=set()
    
    @property      
    def value(self):
        if self.v == "Own Data" or self.v == "Own data":
            return 17
        if self.v == "No protection":
            return 1
        if self.v == "-":
            return 1
        if self.v != None and self.v != "" and floatv(self.v) != 0:
            return self.v
        elif self.f:
            self.v = self.f()
            return self.v
        else:
            return self.v
    
    @value.setter
    def value(self,v):
        self.v = v
        # for c in self.rdeps:
        #     c.rreset(set([self]))
    
    def __str__(self):
        return self.__repr__()
    
    def __repr__(self):
        return f"{self.sheet.name}!{self.name} is {self.v}"
    
    def reset(self):
        if(self.f):
            self.v = None
            # self.v = self.f()

    def rreset(self,cells=None):
        self.v = None
        if(self in cells):
            return
        for c in self.rdeps: #deps 是依赖于该cell的cell的列表 可以是set。
            xcells=set(cells)
            xcells.add(self)
            c.rreset(xcells)

    def update_rdeps(self):
        for  c  in self.deps:
            c = self.sheet.workbook.cell(c)
            c.rdeps.add(self)

    def renew(self):
        if(self.f):
            self.v = self.f()
  
    def isDep(self,cell):
        return cell in self.deps
     
class xWorksheet:
    def __init__(self,name,wb):
        self.name = name
        self.cells={}
        self.workbook = wb
        self._rows=[]
        for r in range(1024):#最大1024行
            rc = [None for i in range(52)]#最大52列A-AZ
            self._rows.append(rc)
        
    def cell(self,name,name2=None):
        if(name.find("$")!=-1):
            name = name.replace("$","")
            
        if(name2):
            name+=str(name2)
        if(name.find("!")!=-1):
            return self.workbook.cell(name)
        
        cell = self.cells.get(name)
        if cell:
            return cell
        
        if name.find(":")!=-1:
            cell = xRange(self,name)
        else:
            cell = xCell(self,name)
            r,c = cell_to_row_col(name)
            self._rows[r-1][c-1]=cell
            
        self.workbook.cells.append(cell)
        self.cells[name]=cell
        return cell
    
    def icell(self,r,c):
        rc = self._rows[r-1]#假定1为索引起始点
        if(rc[c-1] is None):
            id = number_to_excel_column(c)+str(r)
            return self.cell(id)
        return rc[c-1]
    
    def xcell(self,r,c=None):
        if not isinstance(r,str):
            return self.icell(r,c)
        return self.cell(r)

    def set_cell(self, name, value):
        self.cells[name].v = value
        
    def load_sheet_xml(self,sheetFile):
        sheet = parse(sheetFile)
        sheet.documentElement
        sheet=sheet.documentElement.getElementsByTagName("sheetData")[0]
        for row in sheet.getElementsByTagName("row"):
            for c in row.getElementsByTagName("c"):
                name = c.getAttribute("r")
                v = c.getElementsByTagName("v")
                if(isinstance(v,list)):
                    if(len(v) > 0):
                        v = v[0]
                        if(len(v.childNodes) > 0):
                            v = v.childNodes[0]
                            v = v.nodeValue
                            text = v
                            v = float(v) if isnumber(v) else v
                            cell = self.cell(name)
                            cell.value = v
                            cell.text = text
                            cell.f = None
class xWorkbook:
    def __init__(self):
        self.worksheets={}
        self.cells=[]
    def worksheet(self,name):
        ws = self.worksheets.get(name)
        if(ws):
            return ws
        ws = xWorksheet(name,self)
        self.worksheets[name]=ws
        return ws
    
    def cell(self,name):
        name = name.split("!")
        s = name[0]
        c = name[1]
        return self.worksheet(s).cell(c)
    
    def icell(self, ws, r, c):
        return self.worksheet(ws).icell(r, c)

    def reset(self):
        for c in self.cells:
            if c.name.find(":") == -1:
                c.reset()
            else:
                for rc in c.cells:
                    rc.reset()
    def update_rdeps(self):
        for c in self.cells:
            c.update_rdeps()