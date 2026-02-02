'''
Date: 2024/06/07
Author: Fengyuan Zhang
Email: franklinzhang@foxmail.com
Description: Main file of BSTEM model

The Bank Toe Erosion Model can be used as a tool for making reasonably informed estimates 
of hydraulic erosion of the bank and bank toe by hydraulic shear stress.  The model is 
primarily intended for use in studies where bank toe erosion threatens bank stability.  
The effects of erosion protection on the bank and toe can be incorporated to show the 
effects of erosion control measures.

The model estimates boundary shear stress from channel geometry, and considers critical 
shear stress and erodibility of two separate zones with potentially different materials: 
the bank and bank toe; the bed elevation is assumed to be fixed. This is because the model 
assumes that erosion is not transport limited and does not incorporate, in any way, the 
simulation of sediment transport.

Input the bank coordinates, flow parameters and channel slope (Input Geometry), then input 
your bed, bank and toe material types and erosion protection (if any) (Bank Material and 
Bank Vegetation and Protection).  Next, run the shear stress macro (Toe Model Output) to 
determine how much erosion may occur during the prescribed storm event.

'''

import math, random
from math import sqrt, atan, pi
import matplotlib.pyplot as plt
# from openpyxl import load_workbook
import modelResource.erosionModel.Excel_source_codes.xcel as xcel
import modelResource.erosionModel.Excel_source_codes.xcel_fx as xcel_fx
from modelResource.erosionModel.Excel_source_codes.xcel_fx import floatv, CDiv
import numpy as np
from copy import deepcopy

cintMaxNumberofPoints = 23
cintNumberofLayers = 5
cintNumberofSlices = 15
cdbl_min_failure_width = 0.1
wb = xcel.xWorkbook()


def initVX(filepath):

    sheets=[                  
        "Introduction" ,"sheet1",
        "Tech Background" ,"sheet2",
        "Model use and FAQ" ,"sheet3",
        "Input Geometry","sheet4",
        "Bank Material","sheet5",
        "Bank Vegetation and Protection","sheet6",
        "Bank Model Output" ,"sheet7",
        "Toe Model Output","sheet8",
        "Unit Converter","sheet9",
        "Toe Model" ,"sheet10",
        "Calculations" ,"sheet11",
        "VertSliceCalcs" ,"sheet12"
    ]

    for i in range(len(sheets)//2):
        name = sheets[i*2]
        file = sheets[i*2 + 1]
        wb.worksheet(name).load_sheet_xml(filepath + file + ".xml")
    xcel_fx.init_workbook(wb)

    return 

class input_geometry_sheet:
    def cell(row, column):
        return xcel_fx.icell(row, column, "Input Geometry")

class calculations_sheet:
    def cell(row, column):
        return xcel_fx.icell(row, column, "Calculations")

class vert_slice_calcs_sheet:
    def cell(row, column):
        return xcel_fx.icell(row, column, "VertSliceCalcs")

class toe_model_sheet:
    def cell(row, column):
        return xcel_fx.icell(row, column, "Toe Model")

class toe_model_output_sheet:
    def cell(row, column):
        return xcel_fx.icell(row, column, "Toe Model Output")

class bank_model_output_sheet:
    def cell(row, column):
        return xcel_fx.icell(row, column, "Bank Model Output")

# View the Bank in plot
def view_bank(x_values, z_values, l_values = ["A","B","C","D","E","F","G","H","I","J","K","L","M","N","O","P","Q","R","S","T","U","V","W"]):
    # Create the plot
    plt.figure(figsize=(8, 6))
    plt.plot(x_values, z_values, marker='o')

    # Set chart properties
    plt.title('Bank Geometry')
    plt.xlabel('STATION (M)')
    plt.ylabel('ELEVATION (M)')
    plt.grid(False)

    # Add data labels for every second point
    for i in range(0, len(x_values), 2):
        plt.text(x_values[i], z_values[i], l_values[i], fontsize=9, fontweight='bold')

    # Show the plot
    plt.show()


#! 这里其实改成的反向操作
def read_bank_geometry(adblBankGeomX, adblBankGeomZ, intToePoint):
    # This function should implement the logic to read the bank geometry.
    # The actual implementation needs to be defined.

    # 初始化变量
    int_read_point = 1
    str_err_msg = "Please check the geometric data you have entered and retry"
    str_err_msg1 = "Use the tick boxes to select a point at the top of the bank toe"

    # 读取输入的几何数据
    if xcel_fx.icell(109, 3, "Input Geometry").value == 2:
        intToePoint = 17

    for int_row in range(114, 114 + cintMaxNumberofPoints):
        # if input_geom_ws.cell(row=int_row, column=5).value is None:
        if xcel_fx.icell(int_row, 5, "Input Geometry").value is None:
            break
        # if input_geom_ws.cell(row=int_row, column=7).value:
        if xcel_fx.icell(int_row, 7, "Input Geometry").value:
            intToePoint = int_read_point
        if not isinstance(float(xcel_fx.icell(int_row, 3, "Input Geometry").value), (int, float)):
            raise ValueError("Invalid or absent geometric data!")
        # adblBankGeomX[int_read_point - 1] = input_geom_ws.cell(row=int_row, column=3).value
        # adblBankGeomZ[int_read_point - 1] = input_geom_ws.cell(row=int_row, column=5).value
        xcel_fx.icell(int_row, 3, "Input Geometry").value = adblBankGeomX[int_read_point - 1]
        xcel_fx.icell(int_row, 5, "Input Geometry").value = adblBankGeomZ[int_read_point - 1]
        # adblBankGeomX[int_read_point - 1] = float(xcel_fx.icell(int_row, 3, "Input Geometry").value)
        # adblBankGeomZ[int_read_point - 1] = float(xcel_fx.icell(int_row, 5, "Input Geometry").value)
        int_read_point += 1

    # 检查用户是否只选择了一个脚趾点
    if intToePoint == 0:
        raise ValueError("Use the tick boxes to select a point at the top of the bank toe")

    # while int_read_point <= cintMaxNumberofPoints:
    #     adblBankGeomX[int_read_point - 1] = -99999999
    #     adblBankGeomZ[int_read_point - 1] = -99999999
    #     int_read_point += 1
    return adblBankGeomX, adblBankGeomZ, intToePoint

def remove_crossing_lines(adbl_bank_geom_x, adbl_bank_geom_z, int_point):
    """
    检查银行配置文件的两个部分是否交叉，并相应地重新排序点
    """
    bln_intersect = False
    cint_max_number_of_points = len(adbl_bank_geom_x)  # 假设已定义最大点数

    int_inner_loop_point = int_point
    while (adbl_bank_geom_x[int_inner_loop_point] != -99999999 and 
           adbl_bank_geom_z[int_inner_loop_point] != -99999999 and 
           cint_max_number_of_points > int_inner_loop_point + 1):

        # 计算分母
        dbl_denominator = (
            (adbl_bank_geom_z[int_inner_loop_point + 1] - adbl_bank_geom_z[int_inner_loop_point]) *
            (adbl_bank_geom_x[int_point + 1] - adbl_bank_geom_x[int_point]) -
            (adbl_bank_geom_x[int_inner_loop_point + 1] - adbl_bank_geom_x[int_inner_loop_point]) *
            (adbl_bank_geom_z[int_point + 1] - adbl_bank_geom_z[int_point])
        )

        # 计算两个分子
        dbl_numerator_a = (
            (adbl_bank_geom_x[int_inner_loop_point + 1] - adbl_bank_geom_x[int_inner_loop_point]) *
            (adbl_bank_geom_z[int_point] - adbl_bank_geom_z[int_inner_loop_point]) -
            (adbl_bank_geom_z[int_inner_loop_point + 1] - adbl_bank_geom_z[int_inner_loop_point]) *
            (adbl_bank_geom_x[int_point] - adbl_bank_geom_x[int_inner_loop_point])
        )
        dbl_numerator_b = (
            (adbl_bank_geom_x[int_point + 1] - adbl_bank_geom_x[int_point]) *
            (adbl_bank_geom_z[int_point] - adbl_bank_geom_z[int_inner_loop_point]) -
            (adbl_bank_geom_z[int_point + 1] - adbl_bank_geom_z[int_point]) *
            (adbl_bank_geom_x[int_point] - adbl_bank_geom_x[int_inner_loop_point])
        )

        # 避免除以零，这表示线条平行或重合
        if round(dbl_denominator, 6) != 0:
            # 计算斜率
            dbl_slope_a = dbl_numerator_a / dbl_denominator
            dbl_slope_b = dbl_numerator_b / dbl_denominator

            # 如果两条线相交，分数点将在0和1之间（含0和1）
            if 0 < dbl_slope_a < 1 and 0 < dbl_slope_b < 1:
                int_first_reordered_point = int_point + 1
                bln_intersect = True
                adbl_reordered_points_x = np.zeros(int_inner_loop_point - int_point + 1)
                adbl_reordered_points_z = np.zeros(int_inner_loop_point - int_point + 1)
                break

        int_inner_loop_point += 1

    if bln_intersect:
        for int_point in range(int_first_reordered_point, int_inner_loop_point + 1):
            adbl_reordered_points_x[int_inner_loop_point - int_point] = adbl_bank_geom_x[int_point]
            adbl_reordered_points_z[int_inner_loop_point - int_point] = adbl_bank_geom_z[int_point]

        for int_point in range(int_first_reordered_point, int_inner_loop_point + 1):
            adbl_bank_geom_x[int_point] = adbl_reordered_points_x[int_point - int_first_reordered_point]
            adbl_bank_geom_z[int_point] = adbl_reordered_points_z[int_point - int_first_reordered_point]

    return adbl_bank_geom_x, adbl_bank_geom_z

def set_bank_layer_intersect(adblX, adblZ):
    """
    计算层与银行轮廓的交点
    """

    # 获取层数和最大点数（假设这两个常量已在代码的其他地方定义）
    cint_max_number_of_points = len(adblX)  # 假设adblX和adblZ的长度相同

    # 遍历每一层
    for int_layer in range(1, cintNumberofLayers + 1):
        # 获取层的高度
        # dbl_top_elevation = calculations_sheet.cell(row=int_layer + 5, column=17).value
        dbl_top_elevation = float(xcel_fx.icell(int_layer + 5, 17, "Calculations").value)

        # 找到围绕层高的银行轮廓点
        int_point = -1
        while int_point + 2 < cint_max_number_of_points:
            int_point += 1
            dbl_elevation1 = adblZ[int_point]
            dbl_elevation2 = adblZ[int_point + 1]
            if dbl_elevation2 < dbl_top_elevation:
                break

        dbl_station1 = adblX[int_point]
        dbl_station2 = adblX[int_point + 1]
        
        if dbl_top_elevation < dbl_elevation2:
            # calculations_sheet.cell(row=int_layer + 5, column=16, value=dbl_station1)
            xcel_fx.icell(int_layer + 5, 16, "Calculations").value = dbl_station1
        else:
            # 计算交点位置并写入活动单元格
            dbl_top_station = dbl_station1 + (dbl_station2 - dbl_station1) * (dbl_top_elevation - dbl_elevation1) / (dbl_elevation2 - dbl_elevation1)
            # calculations_sheet.cell(row=int_layer + 5, column=16, value=dbl_top_station)
            xcel_fx.icell(int_layer + 5, 16, "Calculations").value = dbl_top_station

def number_of_layers_in_bank(dblBaseElevation):

    # 初始化变量
    number_of_layers_in_bank = 0

    # 遍历每一层
    for int_layer in range(1, cintNumberofLayers + 1):
        # dbl_top_elevation = calculations_sheet.cell(row=28 + int_layer, column=4).value
        dbl_top_elevation = floatv(xcel_fx.icell(28 + int_layer, 4, "Calculations").value)
        if dbl_top_elevation <= dblBaseElevation:
            break
        else:
            number_of_layers_in_bank += 1

    return number_of_layers_in_bank

def set_updated_bank_geometry(adblBankGeomX, adblBankGeomZ, intToePoint):
    # This function should implement the logic to set the updated bank geometry.
    # The actual implementation needs to be defined.

    # # 取消选择脚趾顶点复选框
    # input_geom_ws.cell(row=113 + int_top_toe_point, column=7).value = "FALSE"

    # 检查是否有重复的点（两个连续点在 +/- 1 mm 以内）
    int_insert_point = 2
    int_number_of_points = 2
    while (adblBankGeomX[int_number_of_points - 1] != -99999999 and 
           adblBankGeomZ[int_number_of_points - 1] != -99999999 and 
           int_number_of_points < cintMaxNumberofPoints):
        if 0.001 > math.sqrt((adblBankGeomX[int_number_of_points - 1] - adblBankGeomX[int_number_of_points - 2]) ** 2 + 
                             (adblBankGeomZ[int_number_of_points - 1] - adblBankGeomZ[int_number_of_points - 2]) ** 2):
            int_point = int_number_of_points - 2
            while (adblBankGeomX[int_point] != -99999999 and 
                   adblBankGeomZ[int_point] != -99999999 and 
                   int_point < cintMaxNumberofPoints - 1):
                adblBankGeomX[int_point] = adblBankGeomX[int_point + 1]
                adblBankGeomZ[int_point] = adblBankGeomZ[int_point + 1]
                int_point += 1
            adblBankGeomX[cintMaxNumberofPoints - 1] = -99999999
            adblBankGeomZ[cintMaxNumberofPoints - 1] = -99999999
            int_number_of_points -= 1
            if intToePoint > int_number_of_points:
                intToePoint -= 1
        int_number_of_points += 1

    # 检查配置文件的任何部分是否交叉
    for int_point in range(1, cintMaxNumberofPoints):
        adblBankGeomX, adblBankGeomZ = remove_crossing_lines(adblBankGeomX, adblBankGeomZ, int_point)

    # 设置层与银行配置文件的交点
    set_bank_layer_intersect(adblBankGeomX, adblBankGeomZ)

    # 处理脚趾。循环读取输入的几何数据。获取输入的脚趾点数
    int_point = intToePoint
    int_number_of_points = 1
    while int_number_of_points <= 6:
        if (adblBankGeomX[intToePoint + int_number_of_points - 1] == -99999999 and 
            adblBankGeomZ[intToePoint + int_number_of_points - 1] == -99999999):
            break
        int_number_of_points += 1
    int_number_of_points -= 1

    # 循环读取点直到配置文件满
    while int_number_of_points <= 5:
        # 确定插入位置
        dbl_max_distance = -99999999
        int_insert_point = intToePoint + 1
        for int_point in range(intToePoint + 1, intToePoint + int_number_of_points):
            distance = math.sqrt((adblBankGeomX[int_point] - adblBankGeomX[int_point - 1]) ** 2 + 
                                 (adblBankGeomZ[int_point] - adblBankGeomZ[int_point - 1]) ** 2)
            if distance > dbl_max_distance:
                dbl_max_distance = distance
                int_insert_point = int_point
        
        # 将int_insert_point下面的所有点向下移动
        for int_point in range(intToePoint + int_number_of_points, int_insert_point, -1):
            adblBankGeomX[int_point + 1] = adblBankGeomX[int_point]
            adblBankGeomZ[int_point + 1] = adblBankGeomZ[int_point]
        
        # 使用周围两个点的均值
        adblBankGeomX[int_insert_point] = 0.5 * (adblBankGeomX[int_insert_point - 1] + adblBankGeomX[int_insert_point])
        adblBankGeomZ[int_insert_point] = 0.5 * (adblBankGeomZ[int_insert_point - 1] + adblBankGeomZ[int_insert_point])
        int_number_of_points += 1

    # 获取河岸部分的最低海拔
    dbl_min_elevation = 99999999
    int_point = 1
    while int_point <= intToePoint:
        if (adblBankGeomX[int_point - 1] == -99999999 and 
            adblBankGeomZ[int_point - 1] == -99999999):
            break
        if dbl_min_elevation > adblBankGeomZ[int_point - 1]:
            dbl_min_elevation = adblBankGeomZ[int_point - 1]
        int_point += 1

    # 确定跨越河岸的层数
    int_number_of_layers = number_of_layers_in_bank(dbl_min_elevation)

    # 循环读取点直到配置文件满
    while intToePoint < cintMaxNumberofPoints - 6:
        # 确定插入位置
        dbl_max_distance = -99999999
        for int_point in range(intToePoint, 3, -1):
            distance = math.sqrt((adblBankGeomX[int_point - 1] - adblBankGeomX[int_point - 2]) ** 2 + 
                                 (adblBankGeomZ[int_point - 1] - adblBankGeomZ[int_point - 2]) ** 2)
            if distance > dbl_max_distance:
                dbl_max_distance = distance
                int_insert_point = int_point

        # 将int_insert_point下面的所有点向下移动
        for int_point in range(intToePoint + int_number_of_points - 1, int_insert_point, -1):
            adblBankGeomX[int_point + 1] = adblBankGeomX[int_point]
            adblBankGeomZ[int_point + 1] = adblBankGeomZ[int_point]

        # 循环读取层和几何数据，在适当位置插入层交点
        for int_layer in range(int_number_of_layers, 0, -1):
            # if (calc_ws.cell(row=5 + int_layer, column=17).value - 1E-15 > adblBankGeomZ[int_insert_point]):
            if (float(xcel_fx.icell(5 + int_layer, 17, "Calculations").value) - 1E-15 > adblBankGeomZ[int_insert_point]):
                break

        # dbl_distance = math.sqrt((adblBankGeomX[int_insert_point] - calc_ws.cell(row=5 + int_layer, column=16).value) ** 2 + 
        #                          (adblBankGeomZ[int_insert_point] - calc_ws.cell(row=5 + int_layer, column=17).value) ** 2)
        dbl_distance = math.sqrt((adblBankGeomX[int_insert_point] - float(xcel_fx.icell(int_layer + 5, 16, "Calculations").value)) ** 2 + 
                                 (adblBankGeomZ[int_insert_point] - float(xcel_fx.icell(int_layer + 5, 17, "Calculations").value)) ** 2)
        if (dbl_max_distance > dbl_distance and dbl_distance > 0.001):
            # adblBankGeomX[int_insert_point] = calc_ws.cell(row=5 + int_layer, column=16).value
            # adblBankGeomZ[int_insert_point] = calc_ws.cell(row=5 + int_layer, column=17).value
            adblBankGeomX[int_insert_point] = float(xcel_fx.icell(int_layer + 5, 16, "Calculations").value)
            adblBankGeomZ[int_insert_point] = float(xcel_fx.icell(int_layer + 5, 17, "Calculations").value)
        else:
            adblBankGeomX[int_insert_point] = 0.5 * (adblBankGeomX[int_insert_point - 1] + adblBankGeomX[int_insert_point])
            adblBankGeomZ[int_insert_point] = 0.5 * (adblBankGeomZ[int_insert_point - 1] + adblBankGeomZ[int_insert_point])
        intToePoint += 1

    # 最后检查重复的海拔并输出新配置文件
    for int_point in range(2, cintMaxNumberofPoints):
        if 1E-06 > abs(adblBankGeomZ[int_point - 1] - adblBankGeomZ[int_point - 2]):
            adblBankGeomZ[int_point - 1] = adblBankGeomZ[int_point - 2] - 1E-06 + (adblBankGeomZ[int_point - 1] - adblBankGeomZ[int_point - 2])

    for int_point in range(1, cintMaxNumberofPoints + 1):
        # input_geom_ws.cell(row=19 + int_point, column=3).value = adblBankGeomX[int_point - 1]
        # input_geom_ws.cell(row=19 + int_point, column=5).value = adblBankGeomZ[int_point - 1]
        xcel_fx.set_icell(19 + int_point, 3, adblBankGeomX[int_point - 1], "Input Geometry")
        xcel_fx.set_icell(19 + int_point, 5, adblBankGeomZ[int_point - 1], "Input Geometry")

    # if (input_geom_ws.cell(row=109, column=3).value == 2 and input_geom_ws.cell(row=28, column=7).value):
    #     input_geom_ws.cell(row=44, column=5).value = input_geom_ws.cell(row=138, column=5).value
    #     input_geom_ws.cell(row=46, column=5).value = input_geom_ws.cell(row=140, column=5).value
    if (xcel_fx.icell(109, 3, "Input Geometry").value == 2 and xcel_fx.icell(28, 7, "Input Geometry").value):
        xcel_fx.icell(44, 5, "Input Geometry").value = xcel_fx.icell(138, 5, "Input Geometry").value
        xcel_fx.icell(46, 5, "Input Geometry").value = xcel_fx.icell(140, 3, "Input Geometry").value

    # input_geom_ws.cell(row=109, column=3).value = 1
    # input_geom_ws.cell(row=130, column=7).value = "TRUE"
    xcel_fx.icell(109, 3, "Input Geometry").value = 1
    xcel_fx.icell(130, 7, "Input Geometry").value = "TRUE"

def set_water_bank_intersect(adblBankGeomX, adblBankGeomZ, dblWaterElevation):
    # 定义变量
    dblElevation1 = 0.0
    dblElevation2 = 0.0
    dblMinElevation = 99999999.0
    dblStation1 = 0.0
    dblStation2 = 0.0
    dblWaterBankIntersectStation = 0.0
    
    # 查找水面高度周围的点
    intPoint = 0
    while cintMaxNumberofPoints > intPoint + 1:
        dblElevation1 = adblBankGeomZ[intPoint]
        dblElevation2 = adblBankGeomZ[intPoint + 1]
        if dblElevation2 <= dblWaterElevation:
            break
        intPoint += 1
    dblStation1 = adblBankGeomX[intPoint]
    dblStation2 = adblBankGeomX[intPoint + 1]
    
    # 检查是否为银行或超银行
    if dblWaterElevation > dblElevation1:
        dblWaterBankIntersectStation = adblBankGeomX[1]
    else:
        # 计算交点的站点
        dblWaterBankIntersectStation = dblStation1 + (dblStation2 - dblStation1) * (dblWaterElevation - dblElevation1) / (dblElevation2 - dblElevation1)
    
    # 设置结果
    for intPoint in range(cintMaxNumberofPoints):
        if dblMinElevation > adblBankGeomZ[intPoint]:
            dblMinElevation = adblBankGeomZ[intPoint]
    
    if dblMinElevation > dblWaterElevation:
        # calculations_sheet['P31'].value = ""
        # calculations_sheet['P32'].value = ""
        # calculations_sheet['Q31'].value = ""
        # calculations_sheet['Q32'].value = ""
        calculations_sheet.cell(row=31, column=16).value = ""
        calculations_sheet.cell(row=32, column=16).value = ""
        calculations_sheet.cell(row=31, column=17).value = ""
        calculations_sheet.cell(row=32, column=17).value = ""
    else:
        # calculations_sheet['P31'].value = dblWaterBankIntersectStation
        # calculations_sheet['P32'].value = adblBankGeomX[cintMaxNumberofPoints - 1]
        # calculations_sheet['Q31'].value = dblWaterElevation
        # calculations_sheet['Q32'].value = dblWaterElevation
        calculations_sheet.cell(row=31, column=16).value = dblWaterBankIntersectStation
        calculations_sheet.cell(row=32, column=16).value = adblBankGeomX[cintMaxNumberofPoints - 1]
        calculations_sheet.cell(row=31, column=17).value = dblWaterElevation
        calculations_sheet.cell(row=32, column=17).value = dblWaterElevation

def set_bank_geometry(adblBankGeomX, adblBankGeomZ, intToePoint):
    # Load the workbook and sheets

    # Variable declarations
    dblBaseElevation = 0
    dblBaseStation = 0
    dblFailureAngle = 0
    dblFPIntersectStation = 0
    dblFPIntersectElevation = 0
    dblWaterBankIntersectStation = 0
    dblWaterElevation = 0
    intIteration = 0
    intOutputColumn = 0
    intOutputRow = 0
    intResponse = 0
    strErrMsg = "The inputted shear surface emerges too low in the bank."
    strErrMsg1 = "The failure plane angle cannot equal zero!"

    # Set the correct output locations
    # if input_geometry_sheet.cell(row=109, column=3).value == 1:
    if xcel_fx.icell(109, 3, "Input Geometry").value == 1:
        intOutputColumn = 5
        intOutputRow = 46
    else:
        intOutputColumn = 7
        intOutputRow = 28
        # if input_geometry_sheet.cell(row=intOutputRow, column=intOutputColumn).value == "":
        if xcel_fx.icell(intOutputRow, intOutputColumn).value == "":
            input_geometry_sheet.cell(row=intOutputRow - 2, column=intOutputColumn).value = ""
        else:
            input_geometry_sheet.cell(row=intOutputRow - 2, column=intOutputColumn).value = input_geometry_sheet.cell(row=130, column=5).value

    # Read inputted bank geometry
    adblBankGeomX, adblBankGeomZ, intToePoint = read_bank_geometry(adblBankGeomX, adblBankGeomZ, intToePoint)

    # # Activate the "Calculations" worksheet
    # calculations_sheet.activate()

    # Update the bank geometry
    set_updated_bank_geometry(adblBankGeomX, adblBankGeomZ, intToePoint)

    # Set intersect of water surface with bank profile
    # dblWaterElevation = calculations_sheet.cell(row=63, column=2).value
    dblWaterElevation = float(xcel_fx.icell(63, 2, "Calculations").value)
    set_water_bank_intersect(adblBankGeomX, adblBankGeomZ, dblWaterElevation)

    # Check if the auto shear angle option has been selected
    if input_geometry_sheet.cell(row=intOutputRow, column=intOutputColumn).value == "" or (intOutputColumn == 5 and input_geometry_sheet.cell(row=44, column=intOutputColumn).value == ""):
        # Set the coordinates of the shear plane to be the bank-most node
        calculations_sheet.cell(row=15, column=16).value = calculations_sheet.cell(row=27, column=6).value
        calculations_sheet.cell(row=16, column=16).value = calculations_sheet.cell(row=27, column=6).value
        vert_slice_calcs_sheet.cell(row=25, column=16).value = calculations_sheet.cell(row=27, column=6).value
        vert_slice_calcs_sheet.cell(row=26, column=16).value = calculations_sheet.cell(row=27, column=6).value
        calculations_sheet.cell(row=15, column=17).value = calculations_sheet.cell(row=27, column=7).value
        calculations_sheet.cell(row=16, column=17).value = calculations_sheet.cell(row=27, column=7).value
        vert_slice_calcs_sheet.cell(row=25, column=17).value = calculations_sheet.cell(row=27, column=7).value
        vert_slice_calcs_sheet.cell(row=26, column=17).value = calculations_sheet.cell(row=27, column=7).value
        vert_slice_calcs_sheet.cell(row=27, column=16).value = ""
        vert_slice_calcs_sheet.cell(row=27, column=17).value = ""
    else:
        # Store the inputted base elevation and failure plane angle
        dblBaseElevation = float(input_geometry_sheet.cell(row=138, column=5).value)
        dblFailureAngle = float(input_geometry_sheet.cell(row=140, column=5).value) * math.pi / 180

        # Check that the base elevation is reasonable
        if input_geometry_sheet.cell(row=135, column=5).value > dblBaseElevation:
            print(strErrMsg)
            # input_geometry_sheet.activate()
            return
        elif dblFailureAngle == 0:
            print(strErrMsg1)
            # input_geometry_sheet.activate()
            return
        else:
            input_geometry_sheet.cell(row=intOutputRow, column=intOutputColumn).value = dblFailureAngle * 180 / math.pi

            # Calculate intersect of failure surface and bank face
            set_bank_shear_intersect_station(intIteration, adblBankGeomX, adblBankGeomZ, dblBaseElevation, dblBaseStation, intOutputRow, intOutputColumn)

            # Calculate intersect of failure surface and floodplain
            dblFPIntersectStation, dblFPIntersectElevation = set_floodplain_shear_intersect(intIteration, adblBankGeomX, adblBankGeomZ, dblBaseStation, dblBaseElevation, dblFailureAngle, dblFPIntersectStation, dblFPIntersectElevation)

    # Set applied shear stresses equal to zero
    for row in range(45, 68):
        toe_model_sheet.cell(row=row, column=2).value = None
    toe_model_output_sheet.cell(row=24, column=15).value = None

def set_undercut_index(adblX, adblZ):

    # 初始化变量
    dblTopStation = adblX[0]
    dblTopElevation = adblZ[0]
    dblToeStation = adblX[cintMaxNumberofPoints - 1]
    dblToeElevation = adblZ[cintMaxNumberofPoints - 1]
    intToePoint = cintMaxNumberofPoints - 1
    intUndercut = cintMaxNumberofPoints - 1
    intUndercutToe = cintMaxNumberofPoints - 1
    dblMaxUndercut = 0
    dblMinStation = dblToeStation
    dblMaxStation = dblToeStation
    blnDirection = False
    intPoint = cintMaxNumberofPoints - 1

    # 找到具有最大悬垂的点
    while intPoint > 0:
        if round(adblX[intPoint], 6) >= round(adblX[intPoint - 1], 6) and not blnDirection:
            # 渠道岸继续向后铺设。增量趾点。
            intToePoint = intPoint
        elif round(adblX[intPoint], 6) < round(adblX[intPoint - 1], 6) and not blnDirection:
            # 渠道岸的面从向后铺设变为悬垂渠。
            # 设置悬垂的山谷侧范围。
            dblMinStation = adblX[intPoint]
            dblMaxStation = adblX[intPoint - 1]
            blnDirection = True
            intUndercutToe = intPoint
        elif round(adblX[intPoint], 6) <= round(adblX[intPoint - 1], 6) and blnDirection:
            # 渠道岸的悬垂在增加，更新悬垂的流边范围。
            dblMaxStation = adblX[intPoint - 1]
        elif round(adblX[intPoint], 6) > round(adblX[intPoint - 1], 6) and blnDirection:
            # 渠道岸的面从悬垂渠变为向后铺设。
            # 检查岸段欠切的程度，如果这是最大悬垂。
            dblDistance = dblMaxStation - dblMinStation
            if dblDistance > dblMaxUndercut:
                dblMaxUndercut = dblDistance
                intUndercut = intPoint
            blnDirection = False
        intPoint -= 1

    return intUndercut, intUndercutToe, dblMaxUndercut

def set_bank_layer_intersect(adblX, adblZ):
    # 遍历各层
    for intLayer in range(1, cintNumberofLayers + 1):
        # 获取层的高程
        dblTopElevation = float(calculations_sheet.cell(row=intLayer + 5, column=17).value)

        # 找到与层高程相邻的银行轮廓点
        intPoint = 0
        while intPoint + 2 < cintMaxNumberofPoints:
            intPoint += 1
            dblElevation1 = adblZ[intPoint]
            dblElevation2 = adblZ[intPoint + 1]
            if dblElevation2 < dblTopElevation:
                break
        
        dblStation1 = adblX[intPoint]
        dblStation2 = adblX[intPoint + 1]
        
        if dblTopElevation < dblElevation2:
            calculations_sheet.cell(row=intLayer + 5, column=16).value = dblStation1
        else:
            # 计算相交点的站点并写入活动单元格
            dblTopStation = dblStation1 + (dblStation2 - dblStation1) * (dblTopElevation - dblElevation1) / (dblElevation2 - dblElevation1)
            calculations_sheet.cell(row=intLayer + 5, column=16).value = dblTopStation

def set_bank_shear_intersect_station(intIteration, adblX, adblZ, dblBaseElevation, dblBaseStation, intOutputRow, intOutputColumn):
    # # 打开Excel工作簿
    # wb = openpyxl.load_workbook(workbook_path)
    # calculations_sheet = wb['Calculations']
    # vert_slice_calcs_sheet = wb['VertSliceCalcs']
    # input_geometry_sheet = wb['Input Geometry']

    # 遍历找到与破坏基高程相邻的坡岸轮廓点
    intPoint = -1
    while intPoint + 2 < cintMaxNumberofPoints:
        intPoint += 1
        dblElevation1 = adblZ[intPoint]
        dblElevation2 = adblZ[intPoint + 1]
        if dblElevation2 <= dblBaseElevation:
            break
    
    dblStation1 = adblX[intPoint]
    dblStation2 = adblX[intPoint + 1]

    # 计算相交点的站点并输出
    dblBaseStation = dblStation1 + (dblStation2 - dblStation1) * CDiv((dblBaseElevation - dblElevation1) , (dblElevation2 - dblElevation1))
    
    calculations_sheet.cell(row=15, column=16).value = dblBaseStation
    vert_slice_calcs_sheet.cell(row=25, column=16).value = dblBaseStation
    calculations_sheet.cell(row=15, column=17).value = dblBaseElevation
    vert_slice_calcs_sheet.cell(row=25, column=17).value = dblBaseElevation
    input_geometry_sheet.cell(row=intOutputRow - 2, column=intOutputColumn).value = dblBaseElevation
    xcel_fx.cells_reset()
    return dblBaseStation

def set_floodplain_shear_intersect(intIteration, adblBankGeomX, adblBankGeomZ, dblBaseStation, dblBaseElevation, dblAngle, dblTopStation, dblTopElevation):
    # # 打开Excel工作簿
    # wb = openpyxl.load_workbook(workbook_path)
    # calculations_sheet = wb['Calculations']
    # vert_slice_calcs_sheet = wb['VertSliceCalcs']
    # input_geometry_sheet = wb['Input Geometry']

    # 设置错误消息
    strErrorMessage = ("The model is unable to determine the intersect of the slip surface with the "
                       "floodplain with the present bank geometry. Adjusting the position of Point A...")
    
    adblX = adblBankGeomX.copy()
    adblZ = adblBankGeomZ.copy()
    
    # 设置滑动面的切线角度
    dblTngFailureAngle = math.tan(dblAngle)
    
    # 如果破坏角度为90度，则不计算dblTopStation
    if 0.5 * math.pi > dblAngle:
        intPoint = len(adblX) - 2
        while intPoint > 1:
            if (round(adblZ[intPoint], 6) >= round(dblBaseElevation, 6) and
                    round(dblBaseStation, 6) > round(adblX[intPoint], 6)):
                break
            intPoint -= 1

        while intPoint > 0:
            dblDistance = dblBaseStation - adblX[intPoint]
            if abs(dblDistance) < 1e-05:
                dblDistance = 1e-05
            dblTngAngle = (adblZ[intPoint] - dblBaseElevation) / dblDistance
            if 0 >= dblTngAngle:
                dblTngAngle = 999999
            if dblTngFailureAngle >= dblTngAngle:
                break
            intPoint -= 1
        
        dblStation1 = adblX[intPoint]
        dblStation2 = adblX[intPoint + 1]
        dblElevation1 = adblZ[intPoint]
        dblElevation2 = adblZ[intPoint + 1]
        # intResponse = MsgBox(strErrorMessage, vbOKOnly, "Error!")
        # Worksheets("Input Geometry").Activate
        # End
        dblTngFPAngle = (dblElevation1 - dblElevation2) / (dblStation1 - dblStation2)
        
        # 计算相交点的站点和高程并输出
        dblTopStation = (dblBaseElevation - dblElevation2 + dblBaseStation * dblTngFailureAngle +
                         dblStation2 * dblTngFPAngle) / (dblTngFailureAngle + dblTngFPAngle)
        dblTopElevation = dblBaseElevation - dblTngFailureAngle * (dblTopStation - dblBaseStation)
        if adblX[0] > dblTopStation:
            adblX[0] = dblTopStation
            adblZ[0] = dblTopElevation
            input_geometry_sheet.cell(row=20, column=3).value = dblTopStation
            input_geometry_sheet.cell(row=20, column=5).value = dblTopElevation
    else:
        # 遍历找到与破坏基站相邻的银行轮廓点
        intPoint = 0
        while intPoint + 1 < len(adblX):
            intPoint += 1
            dblStation1 = adblX[intPoint]
            dblStation2 = adblX[intPoint + 1]
            if dblStation2 > dblBaseStation:
                break
        dblElevation1 = adblZ[intPoint]
        dblElevation2 = adblZ[intPoint + 1]
        
        # 计算相交点的站点和高程并输出
        dblTopStation = dblBaseStation
        dblTopElevation = dblElevation1 + (dblElevation2 - dblElevation1) * (dblTopStation - dblStation1) / (dblStation2 - dblStation1)

    calculations_sheet.cell(row=16, column=16).value = dblTopStation
    vert_slice_calcs_sheet.cell(row=26, column=16).value = dblTopStation
    calculations_sheet.cell(row=16, column=17).value = dblTopElevation
    vert_slice_calcs_sheet.cell(row=26, column=17).value = dblTopElevation
    vert_slice_calcs_sheet.cell(row=27, column=16).value = ""
    vert_slice_calcs_sheet.cell(row=27, column=17).value = ""

    return dblTopStation, dblTopElevation

def set_water_force(intIteration, intNumberofLayers, adblX, adblZ, dblBaseStation, dblBaseElevation, dblWaterElevation,
                    dblWaterBankIntersectStation, dblConfiningForce, dblConfiningAngle):
    """
    这个函数计算每一层土壤层的约束力及其方向。

    参数:
    intIteration (int): 迭代次数。
    intNumberofLayers (int): 层数。
    adblX (list): X坐标的列表。
    adblZ (list): Z坐标的列表。
    dblBaseStation (float): 基站。
    dblBaseElevation (float): 基高程。
    dblWaterElevation (float): 水面高程。
    dblWaterBankIntersectStation (float): 水-银行相交站。
    dblConfiningForce (list): 约束力列表。
    dblConfiningAngle (list): 约束角列表。
    workbook_path (str): Excel文件路径。

    返回:
    None
    """
    # 打开Excel工作簿
    # wb = openpyxl.load_workbook(workbook_path)
    # calculations_sheet = wb['Calculations']

    # 检查水面高程是否低于破坏面的基底
    if dblWaterElevation <= dblBaseElevation:
        # 水面高程低于滑移面的基底。将所有约束力及其角度设为零
        for intLayer in range(1, intNumberofLayers + 1):
            dblConfiningForce[intLayer - 1] = 0
            dblConfiningAngle[intLayer - 1] = 0
            calculations_sheet.cell(row=69, column=intLayer + 1).value = dblConfiningForce[intLayer - 1]  # Force
            calculations_sheet.cell(row=70, column=intLayer + 1).value = dblConfiningAngle[intLayer - 1]  # Angle
    else:
        # 循环遍历每一层以确定约束力及角度
        # 首先找到刚好在滑移面上的银行点
        intPoint = 1
        while intPoint < len(adblX) - 1:
            if adblZ[intPoint] < dblBaseElevation:
                break
            intPoint += 1
        intPoint -= 1

        for intLayer in range(intNumberofLayers, 0, -1):
            # 初始化约束力分量为零
            dblHorizontalComponent = 0
            dblVerticalComponent = 0

            # 设置土层的顶部和底部坐标
            if intLayer == intNumberofLayers:
                # 滑移面底部
                dblBottomElevation = dblBaseElevation
                dblBottomStation = dblBaseStation
            else:
                # 土层底部
                dblBottomElevation = float(calculations_sheet.cell(row=5 + intLayer, column=17).value)
                dblBottomStation = float(calculations_sheet.cell(row=5 + intLayer, column=16).value)

            if dblWaterElevation < float(calculations_sheet.cell(row=28 + intLayer, column=4).value):
                # 水面和银行剖面相交
                dblTopElevation = dblWaterElevation
                dblTopStation = dblWaterBankIntersectStation
            else:
                # 土层顶部
                dblTopElevation = float(calculations_sheet.cell(row=4 + intLayer, column=17).value)
                dblTopStation = float(calculations_sheet.cell(row=4 + intLayer, column=16).value)

            # 循环遍历银行剖面以计算约束力
            dblElevation1 = dblBottomElevation
            dblStation1 = dblBottomStation
            dblTopPressure = 9.807 * (dblWaterElevation - dblElevation1)
            if intPoint > 1:
                while adblZ[intPoint] < dblTopElevation:
                    dblElevation2 = dblElevation1
                    dblStation2 = dblStation1
                    dblBottomPressure = dblTopPressure
                    dblElevation1 = adblZ[intPoint]
                    dblStation1 = adblX[intPoint]
                    dblTopPressure = 9.807 * (dblWaterElevation - dblElevation1)
                    dblDeltaX = dblStation2 - dblStation1
                    dblDeltaZ = dblElevation1 - dblElevation2
                    dblPressure = 0.5 * (dblTopPressure + dblBottomPressure)
                    dblHorizontalComponent += dblPressure * dblDeltaZ
                    dblVerticalComponent += dblPressure * dblDeltaX
                    intPoint -= 1

            # 添加最后一段
            dblElevation2 = dblElevation1 * 1.000000
            #! Check this
            dblStation2 = dblStation1 * 1.000000
            dblBottomPressure = dblTopPressure * 1.000000
            dblElevation1 = dblTopElevation * 1.000000
            dblStation1 = dblTopStation * 1.000000
            dblTopPressure = 9.807 * (dblWaterElevation - dblElevation1)
            #! Check this
            dblDeltaX = dblStation2 - dblStation1
            dblDeltaZ = dblElevation1 - dblElevation2
            dblPressure = 0.5 * (dblTopPressure + dblBottomPressure)
            dblHorizontalComponent += dblPressure * dblDeltaZ
            dblVerticalComponent += dblPressure * dblDeltaX

            # 计算约束力及其角度，并写入电子表格
            dblConfiningForce[intLayer - 1] = math.sqrt(dblHorizontalComponent ** 2 + dblVerticalComponent ** 2)
            if dblVerticalComponent == 0:
                dblConfiningAngle[intLayer - 1] = 0.5 * pi
            else:
                dblConfiningAngle[intLayer - 1] = atan(dblHorizontalComponent / dblVerticalComponent)
                if dblConfiningAngle[intLayer - 1] < 0:
                    dblConfiningAngle[intLayer - 1] += pi

            calculations_sheet.cell(row=69, column=intLayer + 1).value = dblConfiningForce[intLayer - 1]
            calculations_sheet.cell(row=70, column=intLayer + 1).value = dblConfiningAngle[intLayer - 1] * 180 / math.pi

            # 如果土层顶部高于水面高程，退出for循环。
            if dblWaterElevation < float(calculations_sheet.cell(row=28 + intLayer, column=4).value):
                break

        # 对水面以上或滑移面基底以下的层将约束力及其角度设为零
        intFirstWetLayer = intLayer - 1
        for intLayer in range(1, intFirstWetLayer + 1):
            dblConfiningForce[intLayer - 1] = 0
            dblConfiningAngle[intLayer - 1] = 0
            calculations_sheet.cell(row=69, column=intLayer + 1).value = dblConfiningForce[intLayer - 1]  # Force
            calculations_sheet.cell(row=70, column=intLayer + 1).value = dblConfiningAngle[intLayer - 1]  # Angle

        for intLayer in range(intNumberofLayers + 1, len(dblConfiningForce) + 1):
            dblConfiningForce[intLayer - 1] = 0
            dblConfiningAngle[intLayer - 1] = 0
            calculations_sheet.cell(row=69, column=intLayer + 1).value = dblConfiningForce[intLayer - 1]  # Force
            calculations_sheet.cell(row=70, column=intLayer + 1).value = dblConfiningAngle[intLayer - 1]  # Angle
    xcel_fx.cells_reset()

    return dblConfiningForce, dblConfiningAngle

def polygon_area(dblPolygonX, dblPolygonY, intNumberofVertices):
    """
    计算多边形的面积。

    参数:
    dblPolygonX (list): X坐标的列表。
    dblPolygonY (list): Y坐标的列表。
    intNumberofVertices (int): 多边形的顶点数。

    返回:
    float: 多边形的面积。
    """
    area = 0.0
    for intVertex in range(intNumberofVertices):
        intNextVertex = (intVertex + 1) % intNumberofVertices
        area += dblPolygonX[intVertex] * dblPolygonY[intNextVertex] - dblPolygonY[intVertex] * dblPolygonX[intNextVertex]

    area = abs(area) * 0.5
    return area

def set_layer_weight(intIteration, intNumberofLayers, adblBankGeomX, adblBankGeomZ, dblBaseStation, dblBaseElevation,
                     dblFPIntersectStation, dblFPIntersectElevation, adblWeight):
    """
    这个函数计算失效块中包含的每一层土壤的重量。

    参数:
    intIteration (int): 迭代次数。
    intNumberofLayers (int): 层数。
    adblBankGeomX (list): 银行几何X坐标的列表。
    adblBankGeomZ (list): 银行几何Z坐标的列表。
    dblBaseStation (float): 基站。
    dblBaseElevation (float): 基高程。
    dblFPIntersectStation (float): FP交叉站。
    dblFPIntersectElevation (float): FP交叉高程。
    adblWeight (list): 重量列表。
    workbook_path (str): Excel文件路径。

    返回:
    None
    """
    # # 打开Excel工作簿
    # wb = openpyxl.load_workbook(workbook_path)
    # calculations_sheet = wb['Calculations']

    # 找到失效块内的第一层
    intFirstLayer = 1
    adblBulkUnitWeight = [0] * intNumberofLayers
    for intLayer in range(intNumberofLayers, 0, -1):
        dblTopElevation = float(calculations_sheet.cell(5 + intLayer, 17).value)
        if dblTopElevation >= dblFPIntersectElevation:
            intFirstLayer = intLayer + 1
            break
        # 获取该层的总体积重
        adblBulkUnitWeight[intLayer - 1] = float(calculations_sheet.cell(row=73, column=1 + intLayer).value)

    adblX = [0] * 25
    adblZ = [0] * 25

    for intLayer in range(intNumberofLayers, intFirstLayer - 1, -1):
        intVertex = 0
        if intLayer == intNumberofLayers:
            adblX[intVertex] = dblBaseStation
            adblZ[intVertex] = dblBaseElevation
            intVertex += 1
        else:
            adblX[intVertex] = dblStationTopRight
            adblZ[intVertex] = dblElevationTopRight
            adblX[intVertex + 1] = dblStationTopLeft
            adblZ[intVertex + 1] = dblElevationTopLeft
            intVertex += 2

        dblStationTopLeft = float(calculations_sheet.cell(row=21 + intLayer, column=16).value)
        dblElevationTopLeft = float(calculations_sheet.cell(row=21 + intLayer, column=17).value)
        if intLayer == intFirstLayer and dblFPIntersectStation >= adblBankGeomX[1]:
            dblStationTopRight = dblFPIntersectStation
            dblElevationTopRight = dblFPIntersectElevation
        else:
            dblStationTopRight = float(calculations_sheet.cell(row=4 + intLayer, column=16).value)
            dblElevationTopRight = float(calculations_sheet.cell(row=4 + intLayer, column=17).value)
            adblX[intVertex] = dblStationTopLeft
            adblZ[intVertex] = dblElevationTopLeft
            intVertex += 1

        adblX[intVertex] = dblStationTopRight
        adblZ[intVertex] = dblElevationTopRight
        intVertex += 1

        intPoint = len(adblBankGeomX) - 1
        while intPoint > 1:
            if adblBankGeomZ[intPoint - 1] > float(dblElevationTopRight):
                break
            intPoint -= 1

        while (adblBankGeomZ[intPoint] > float(calculations_sheet.cell(row=5 + intLayer, column=17).value) and
               intPoint + 1 < len(adblBankGeomX) and adblBankGeomZ[intPoint] > dblBaseElevation):
            adblX[intVertex] = adblBankGeomX[intPoint]
            adblZ[intVertex] = adblBankGeomZ[intPoint]
            intVertex += 1
            intPoint += 1

        adblWeight[intLayer - 1] = polygon_area(adblX, adblZ, intVertex)
        calculations_sheet.cell(row=35 + intLayer, column=4).value = adblWeight[intLayer - 1]
        adblWeight[intLayer - 1] *= adblBulkUnitWeight[intLayer - 1]
        xcel_fx.cells_reset()

    for intLayer in range(intNumberofLayers + 1, len(adblWeight) + 1):
        adblWeight[intLayer - 1] = 0
        calculations_sheet.cell(row=35 + intLayer, column=4).value = adblWeight[intLayer - 1]

    for intLayer in range(1, intFirstLayer):
        adblWeight[intLayer - 1] = 0
        calculations_sheet.cell(row=35 + intLayer, column=4).value = adblWeight[intLayer - 1]

    xcel_fx.cells_reset()

    return adblWeight

def set_pore_water_force(int_iteration, int_number_of_layers, dbl_base_elevation, 
                         dbl_fp_intersect_elevation, dbl_failure_angle, adbl_friction, adbl_phib, adbl_pore_water_force):
    """
    计算每层土壤层的孔隙水力，并调整材料的总体重
    """
    cdbl_angular_coeff = -0.063

    for int_layer in range(1, int_number_of_layers + 1):
        # 计算层的顶和底的高程
        dbl_layer_top_elevation = calculations_sheet.cell(row=int_layer + 4, column=17).value
        dbl_layer_bottom_elevation = calculations_sheet.cell(row=int_layer + 5, column=17).value

        if dbl_layer_top_elevation > dbl_base_elevation:
            adbl_pore_water_force[int_layer - 1] = input_geometry_sheet.cell(row=91 + int_layer, column=13).value
        else:
            adbl_pore_water_force[int_layer - 1] = 0

        # 计算此层内的失败面长度
        if dbl_fp_intersect_elevation >= dbl_layer_top_elevation:
            dbl_length = (dbl_layer_top_elevation - max(dbl_base_elevation, dbl_layer_bottom_elevation)) / math.sin(dbl_failure_angle)
        else:
            dbl_length = (dbl_fp_intersect_elevation - dbl_layer_bottom_elevation) / math.sin(dbl_failure_angle)

        if dbl_length < 0:
            dbl_length = 0

        # 计算基质吸力或正孔隙水压力
        if adbl_pore_water_force[int_layer - 1] > 0:
            adbl_pore_water_force[int_layer - 1] = -dbl_length * adbl_pore_water_force[int_layer - 1] * math.tan(adbl_phib[int_layer - 1] * math.pi / 180)
        else:
            adbl_pore_water_force[int_layer - 1] = -dbl_length * adbl_pore_water_force[int_layer - 1] * math.tan(adbl_friction[int_layer - 1] * math.pi / 180)
    return adbl_pore_water_force

def set_bank_face_shear_intersect(int_iteration, adbl_x, adbl_z, dbl_base_station, dbl_base_elevation, dbl_angle, dbl_top_station, dbl_top_elevation, int_output_row, int_output_column):
    """
    计算失败面与河岸剖面的交点，并输出结果到指定单元格
    """
    cint_max_number_of_points = len(adbl_x)
    cdbl_pi = math.pi

    dbl_tng_failure_angle = math.tan(-dbl_angle)

    if dbl_angle < 0.5 * cdbl_pi:
        int_point = 1
        while int_point < cint_max_number_of_points:
            int_point += 1
            dbl_distance = adbl_x[int_point] - dbl_top_station
            if abs(dbl_distance) < 0.00001:
                dbl_distance = 0.00001
            dbl_tng_angle = (adbl_z[int_point] - dbl_top_elevation) / dbl_distance
            if (round(dbl_tng_failure_angle, 6) >= round(dbl_tng_angle, 6)) or (dbl_tng_angle >= 0):
                break
        
        dbl_station1 = adbl_x[int_point - 1]
        dbl_station2 = adbl_x[int_point]
        dbl_elevation1 = adbl_z[int_point - 1]
        dbl_elevation2 = adbl_z[int_point]
        
        if dbl_station1 == dbl_station2:
            dbl_tng_bank_angle = 999999
        else:
            dbl_tng_bank_angle = (dbl_elevation1 - dbl_elevation2) / (dbl_station1 - dbl_station2)

        dbl_base_station = (dbl_elevation1 - dbl_top_elevation - dbl_tng_bank_angle * dbl_station1 + dbl_top_station * dbl_tng_failure_angle) / (dbl_tng_failure_angle - dbl_tng_bank_angle)
        dbl_base_elevation = dbl_top_elevation - dbl_tng_failure_angle * (dbl_top_station - dbl_base_station)
    else:
        int_point = 0
        while int_point + 1 < cint_max_number_of_points:
            int_point += 1
            dbl_station1 = adbl_x[int_point]
            dbl_station2 = adbl_x[int_point + 1]
            if dbl_station2 > dbl_base_station:
                break
        
        dbl_elevation1 = adbl_z[int_point]
        dbl_elevation2 = adbl_z[int_point + 1]
        
        dbl_base_station = dbl_top_station
        dbl_base_elevation = dbl_elevation1 + (dbl_elevation2 - dbl_elevation1) * (dbl_base_station - dbl_station1) / (dbl_station2 - dbl_station1)
    
    input_geometry_sheet.cell(row=int_output_row - 2, column=int_output_column, value=dbl_base_elevation)
    calculations_sheet.cell(row=15, column=16, value=dbl_base_station)
    vert_slice_calcs_sheet.cell(row=25, column=16, value=dbl_base_station)
    calculations_sheet.cell(row=15, column=17, value=dbl_base_elevation)
    vert_slice_calcs_sheet.cell(row=25, column=17, value=dbl_base_elevation)
    return dbl_base_station, dbl_base_elevation

def compute_fos(int_iteration, int_loop, int_number_of_layers, adbl_bank_geom_x, adbl_bank_geom_z, 
                adbl_c_prime, adbl_friction, adbl_phib, dbl_base_station, dbl_base_elevation, 
                dbl_failure_angle, dbl_fp_intersect_station, dbl_fp_intersect_elevation, 
                dbl_water_elevation, dbl_water_bank_intersect_station, 
                adbl_confining_force, adbl_confining_angle, adbl_weight, 
                int_output_row, int_output_column):
    """
    计算安全系数
    """
    adbl_pore_water_force = [0] * int_number_of_layers
    dbl_sum_driving_forces = 0
    dbl_sum_resisting_forces = 0
    
    # 设置失败角度
    input_geometry_sheet.cell(row=int_output_row, column=int_output_column).value = dbl_failure_angle * 180 / math.pi

    xcel_fx.cells_reset()
    
    # 根据循环类型设置交点
    if int_loop == 1:
        dbl_base_station = set_bank_shear_intersect_station(int_iteration, adbl_bank_geom_x, adbl_bank_geom_z, dbl_base_elevation, dbl_base_station, int_output_row, int_output_column)
    elif int_loop == 2:
        dbl_base_station, dbl_base_elevation = set_bank_face_shear_intersect(int_iteration, adbl_bank_geom_x, adbl_bank_geom_z, dbl_base_station, dbl_base_elevation, dbl_failure_angle, dbl_fp_intersect_station, dbl_fp_intersect_elevation, int_output_row, int_output_column)
    
    # 计算跨越失败块的层数
    int_number_of_layers = number_of_layers_in_bank(dbl_base_elevation)
    
    # 计算失败面和洪泛区的交点
    dbl_fp_intersect_station, dbl_fp_intersect_elevation = set_floodplain_shear_intersect(int_iteration, adbl_bank_geom_x, adbl_bank_geom_z, dbl_base_station, dbl_base_elevation, dbl_failure_angle, dbl_fp_intersect_station, dbl_fp_intersect_elevation)
    
    # 计算约束力和角度
    adbl_confining_force, adbl_confining_angle = set_water_force(int_iteration, int_number_of_layers, adbl_bank_geom_x, adbl_bank_geom_z, dbl_base_station, dbl_base_elevation, dbl_water_elevation, dbl_water_bank_intersect_station, adbl_confining_force, adbl_confining_angle)
    
    # 计算层的孔隙水力
    adbl_pore_water_force = set_pore_water_force(int_iteration, int_number_of_layers, dbl_base_elevation, dbl_fp_intersect_elevation, dbl_failure_angle, adbl_friction, adbl_phib, adbl_pore_water_force)
    
    # 计算层的面积
    adbl_weight = set_layer_weight(int_iteration, int_number_of_layers, adbl_bank_geom_x, adbl_bank_geom_z, dbl_base_station, dbl_base_elevation, dbl_fp_intersect_station, dbl_fp_intersect_elevation, adbl_weight)
    
    # 计算驱动力和抗力
    for int_layer in range(int_number_of_layers):
        dbl_resisting_forces = (adbl_weight[int_layer] * math.cos(dbl_failure_angle) + adbl_confining_force[int_layer] * math.cos(adbl_confining_angle[int_layer] - dbl_failure_angle)) * math.tan(adbl_friction[int_layer] * math.pi / 180) - adbl_pore_water_force[int_layer]
        if dbl_resisting_forces < 0:
            dbl_resisting_forces = 0
        dbl_driving_forces = adbl_weight[int_layer] * math.sin(dbl_failure_angle) - adbl_confining_force[int_layer] * math.sin(adbl_confining_angle[int_layer] - dbl_failure_angle)

        dbl_sum_resisting_forces += dbl_resisting_forces
        dbl_sum_driving_forces += dbl_driving_forces

    # Prevent positive pore-water pressure from exceeding the weight of the block
    # if dbl_sum_resisting_forces < 0:
    #     dbl_sum_resisting_forces = 0
    xcel_fx.cells_reset()
    # Now add the remaining resisting components (c'L + P cos(a-b) tan f')
    for int_layer in range(1, 6, 1):
        # Compute length of failure plane within this layer
        if dbl_fp_intersect_elevation >= float(calculations_sheet.cell(int_layer + 4, 17).value):
            dbl_length = (float(calculations_sheet.cell(int_layer + 4, 17).value) - max(dbl_base_elevation, float(calculations_sheet.cell(int_layer + 5, 17).value))) / math.sin(dbl_failure_angle)
        else:
            dbl_length = (dbl_fp_intersect_elevation - float(calculations_sheet.cell(int_layer + 5, 17).value)) / math.sin(dbl_failure_angle)
        
        if dbl_length < 0:
            dbl_length = 0

        dbl_sum_resisting_forces += adbl_c_prime[int_layer - 1] * dbl_length

    # If Denominator of Factor of Safety equation <= 0 Then set it to the Failure Angle
    if dbl_sum_driving_forces <= 0:
        dbl_sum_driving_forces = -1

    # Calculate the Factor of Safety
    compute_fos = dbl_sum_resisting_forces / dbl_sum_driving_forces
    if compute_fos <= 0:
        compute_fos = 99999999

    return compute_fos, dbl_fp_intersect_station, dbl_fp_intersect_elevation


def compute_max_angle(iteration, int_number_of_layers, dbl_base_elevation, dbl_base_station, dbl_fp_intersect_station, dbl_fp_intersect_elevation, adbl_bank_geom_x, adbl_bank_geom_z):
    """
    计算最大失败平面角度
    """
    # 初始化变量
    dbl_max_angle = 0.5 * math.pi
    int_point = 1
    
    # 找到在失败平面基底上方的第一个节点
    while int_point < cintMaxNumberofPoints:
        if round(dbl_base_elevation, 6) >= round(adbl_bank_geom_z[int_point - 1], 6):
            break
        int_point += 1
    int_point -= 1

    # 从失败平面基底上方的第一个节点循环到第二个节点，计算银行的最小角度（这是最大失败平面角度）
    int_limiting_point = 1
    while int_point > 1:
        dbl_length = dbl_base_station - adbl_bank_geom_x[int_point - 1]
        if dbl_length < 0.00001:
            dbl_angle = 0.5 * math.pi
        else:
            dbl_angle = math.atan((adbl_bank_geom_z[int_point - 1] - dbl_base_elevation) / dbl_length)
        if dbl_max_angle > dbl_angle:
            int_limiting_point = int_point
            dbl_max_angle = dbl_angle
        int_point -= 1

    # 最小角度差为2度，减小最大角度
    dbl_reduced_angle = math.pi / 90
    if int_limiting_point < 2:
        dbl_fp_intersect_station, dbl_fp_intersect_elevation = set_floodplain_shear_intersect(iteration, adbl_bank_geom_x, adbl_bank_geom_z, dbl_base_station, dbl_base_elevation, dbl_max_angle, dbl_fp_intersect_station, dbl_fp_intersect_elevation)
        
        if cdbl_min_failure_width > (adbl_bank_geom_x[1] - dbl_fp_intersect_station):
            dbl_reduced_angle = math.atan(abs(adbl_bank_geom_x[1] - dbl_base_station + cdbl_min_failure_width) / (dbl_fp_intersect_elevation - dbl_base_elevation))
    
    if (0.5 * math.pi > dbl_max_angle) or (dbl_reduced_angle > math.pi / 90):
        dbl_max_angle = dbl_max_angle - dbl_reduced_angle
    else:
        dbl_max_angle = 0.5 * math.pi

    return dbl_max_angle, dbl_fp_intersect_station, dbl_fp_intersect_elevation

def compute_min_angle(int_number_of_layers, dbl_base_elevation, adbl_friction):
    """
    计算给定基础高程的最小角度
    计算加权平均的phi'值。这是最小的失败平面角度。
    """
    # 初始变量
    dbl_sum_length = 0.0
    compute_min_angle = 0.0

    # 遍历所有的银行配置层
    for int_layer in range(1, int_number_of_layers):
        dbl_length = floatv(calculations_sheet.cell(row=4 + int_layer, column=17).value) - floatv(calculations_sheet.cell(row=5 + int_layer, column=17).value)
        dbl_sum_length += dbl_length
        compute_min_angle += adbl_friction[int_layer - 1] * dbl_length  # 注意这里的索引

    # 最后一层的处理
    dbl_length = floatv(calculations_sheet.cell(row=4 + int_number_of_layers, column=17).value) - dbl_base_elevation
    dbl_sum_length += dbl_length
    compute_min_angle += adbl_friction[int_number_of_layers - 1] * dbl_length  # 注意这里的索引

    # 将计算结果转换为弧度并归一化
    compute_min_angle = compute_min_angle * math.pi / (180 * dbl_sum_length)

    return compute_min_angle

def compute_minimum_fos(iteration, number_of_layers, bank_geom_x, bank_geom_z, base_station, best_base_elevation,
                        best_failure_angle, fp_intersect_station, fp_intersect_elevation, undercut_toe,
                        water_elevation, water_bank_intersect_station, confining_force, confining_angle, weight,
                        dbl_best_fos, output_row, output_column):
    
    # Error messages
    err_msg = "The bank angle is less than the friction angle! The bank should not fail in this situation"
    
    # Local Declarations
    c_prime = np.zeros(cintNumberofLayers)
    friction = np.zeros(cintNumberofLayers)
    phib = np.zeros(cintNumberofLayers)
    bln_better = False
    bln_groundwater_run = False
    dbl_best_fos_stored = float('inf')
    dbl_new_failure_angle = 0
    dbl_new_fos = 0
    int_base_point = 0
    
    # Provide the user with some output
    print("Finding the minimum Factor of Safety...")
    
    # Get the cohesion, friction angle and phi b values
    for layer in range(cintNumberofLayers):
        c_prime[layer] = calculations_sheet.cell(row=13 + layer + 1, column=4).value
        friction[layer] = calculations_sheet.cell(row=8 + layer + 1, column=4).value
        phib[layer] = calculations_sheet.cell(row=18 + layer + 1, column=4).value
    
    # Set the initial location of the base of the failure plane
    if input_geometry_sheet.cell(row=109, column=3).value == 1:
        int_base_point = cintMaxNumberofPoints - 2
    else:
        int_base_point = cintMaxNumberofPoints - 4
    
    # March up the bank
    for search in range(int_base_point, 2, -1):
        base_elevation = bank_geom_z[search]
        
        # Calculate intersect of failure surface and bank face
        base_station = set_bank_shear_intersect_station(iteration, bank_geom_x, bank_geom_z, base_elevation, base_station, output_row, output_column)
        
        # Determine how many layers span the failure block
        number_of_layers = number_of_layers_in_bank(base_elevation)
        
        # Set the minimum angle
        min_angle = compute_min_angle(number_of_layers, base_elevation, friction)
        
        # Find the valleyward bank angle. This is the maximum failure plane angle
        max_angle, fp_intersect_station, fp_intersect_elevation = compute_max_angle(iteration, number_of_layers, base_elevation, base_station, fp_intersect_station, fp_intersect_elevation, bank_geom_x, bank_geom_z)
        
        # Set the initial failure angle equal to the mean of the weighted mean phi prime and bank angle values
        if max_angle > min_angle:
            new_failure_angle = 0.5 * (max_angle + min_angle)
            
            # Compute FoS
            new_fos, fp_intersect_station, fp_intersect_elevation = compute_fos(iteration, 1, number_of_layers, bank_geom_x, bank_geom_z, c_prime, friction, phib, base_station, base_elevation, new_failure_angle, fp_intersect_station, fp_intersect_elevation, water_elevation, water_bank_intersect_station, confining_force, confining_angle, weight, output_row, output_column)
            
            # Compare with stored value and store optimal values
            if new_fos < dbl_best_fos:
                dbl_best_fos = new_fos
                best_failure_angle = new_failure_angle
                best_base_elevation = base_elevation
    
    # Catch the situation where the bank angle is too low for failure to occur
    if best_failure_angle == 0:
        print(err_msg)
        calculations_sheet.cell(row=15, column=16).value = calculations_sheet.cell(row=27, column=6).value
        calculations_sheet.cell(row=16, column=16).value = calculations_sheet.cell(row=27, column=6).value
        vert_slice_calcs_sheet.cell(row=25, column=16).value = calculations_sheet.cell(row=27, column=6).value
        vert_slice_calcs_sheet.cell(row=26, column=16).value = calculations_sheet.cell(row=27, column=6).value
        calculations_sheet.cell(row=15, column=17).value = calculations_sheet.cell(row=27, column=7).value
        calculations_sheet.cell(row=16, column=17).value = calculations_sheet.cell(row=27, column=7).value
        vert_slice_calcs_sheet.cell(row=25, column=17).value = calculations_sheet.cell(row=27, column=7).value
        vert_slice_calcs_sheet.cell(row=26, column=17).value = calculations_sheet.cell(row=27, column=7).value
        vert_slice_calcs_sheet.cell(row=27, column=16).value = ""
        vert_slice_calcs_sheet.cell(row=27, column=17).value = ""
        return
    xcel_fx.cells_reset()

    # Enter the minimization loop
    while(abs(dbl_best_fos - dbl_best_fos_stored) > 0.000001):
        base_elevation = best_base_elevation
        
        # Calculate intersect of failure surface and bank face
        base_station = set_bank_shear_intersect_station(iteration, bank_geom_x, bank_geom_z, base_elevation, base_station, output_row, output_column)
        
        # Determine how many layers span the failure block
        number_of_layers = number_of_layers_in_bank(base_elevation)
        
        # Compute confining force and angle. This only needs to be done once for each failure base position
        # set_water_force(iteration, number_of_layers, bank_geom_x, bank_geom_z, base_station, base_elevation, water_elevation,
        #                 water_bank_intersect_station, confining_force, confining_angle)
        
        # Set the minimum angle
        min_angle = compute_min_angle(number_of_layers, base_elevation, friction)
        
        # Find the valleyward bank angle. This is the maximum failure plane angle
        max_angle, fp_intersect_station, fp_intersect_elevation = compute_max_angle(iteration, number_of_layers, base_elevation, base_station, fp_intersect_station, fp_intersect_elevation, bank_geom_x, bank_geom_z)
        
        # Set the initial angle range and store initial Factor of Safety
        dbl_new_angle_range = max_angle - min_angle
        angle_range_stored = dbl_new_angle_range
        dbl_best_fos_stored = dbl_best_fos
        
        #!!!!!!!!!!!!!!!!! Start the first loop
        while dbl_new_angle_range > 0.005 * angle_range_stored:
            bln_better = False
            old_angle_range = dbl_new_angle_range
            
            # Determine the failure angle and output it to the spreadsheet
            random_angle = (random.random() - 0.5) * dbl_new_angle_range
            for search in [-1, 1]:
                if bln_better:
                    new_failure_angle = best_failure_angle + 2 * random_angle * search
                else:
                    new_failure_angle = best_failure_angle + random_angle * search
                new_failure_angle = max(min(new_failure_angle, max_angle), min_angle)
                
                # Compute FoS
                new_fos, fp_intersect_station, fp_intersect_elevation = compute_fos(iteration, 1, number_of_layers, bank_geom_x, bank_geom_z, c_prime, friction, phib, base_station, base_elevation, new_failure_angle, fp_intersect_station, fp_intersect_elevation, water_elevation, water_bank_intersect_station, confining_force, confining_angle, weight, output_row, output_column)
                
                # Compare with stored value and store optimal values
                if new_fos < dbl_best_fos:
                    bln_better = True
                    dbl_best_fos = new_fos
                    best_failure_angle = new_failure_angle
            
            if bln_better:
                dbl_new_angle_range = old_angle_range * 5 / 3
            else:
                dbl_new_angle_range = old_angle_range / 3

        #!!!!!!!!!!!!!!!!! End the first loop
                
        # Set the minimum angle
        min_angle = compute_min_angle(number_of_layers, base_elevation, friction)
        
        # Find the valleyward bank angle. This is the maximum failure plane angle
        max_angle, fp_intersect_station, fp_intersect_elevation = compute_max_angle(iteration, number_of_layers, base_elevation, base_station, fp_intersect_station,
                                      fp_intersect_elevation, bank_geom_x, bank_geom_z)
        
        # Set the initial angle range
        dbl_new_angle_range = max_angle - min_angle
        angle_range_stored = dbl_new_angle_range
        
        #!!!!!!!!!!!!!!!!! Start Second Loop
        while (dbl_new_angle_range > 0.005 * angle_range_stored):
            bln_better = False
            dbl_old_angle_range = dbl_new_angle_range

            # Determine the failure angle and output it to the spreadsheet
            random.seed()
            dbl_rand_angle = (random.random() - 0.5) * dbl_new_angle_range
            for int_search in range(-1, 2, 2):
                if bln_better:
                    dbl_new_failure_angle = best_failure_angle + 2 * dbl_rand_angle * int_search
                else:
                    dbl_new_failure_angle = best_failure_angle + dbl_rand_angle * int_search

                if dbl_new_failure_angle > max_angle:
                    dbl_new_failure_angle = max_angle
                elif min_angle > dbl_new_failure_angle:
                    dbl_new_failure_angle = min_angle

                # Compute Fs
                dbl_new_fos, fp_intersect_station, fp_intersect_elevation = compute_fos(iteration, 1, number_of_layers, bank_geom_x, bank_geom_z, c_prime, friction, phib, base_station, base_elevation, new_failure_angle, fp_intersect_station, fp_intersect_elevation, water_elevation, water_bank_intersect_station, confining_force, confining_angle, weight, output_row, output_column)

                # Compare with stored value and store optimal values
                if dbl_new_fos < dbl_best_fos:
                    bln_better = True
                    dbl_best_fos = dbl_new_fos
                    best_failure_angle = dbl_new_failure_angle
                    best_base_elevation = base_elevation

            if bln_better:
                dbl_new_angle_range = dbl_old_angle_range * 5 / 3
            else:
                dbl_new_angle_range = dbl_old_angle_range / 3
        #!!!!!!!!!!!!!!!!! End Second Loop
        iteration = iteration + 1

    input_geometry_sheet.cell(row=output_row - 2, column=output_column).value = best_base_elevation
    input_geometry_sheet.cell(row=output_row, column=output_column).value = best_failure_angle * 180 / math.pi

    set_bank_shear_intersect_station(iteration, bank_geom_x, bank_geom_z, best_base_elevation, base_station, output_row, output_column)
    int_number_of_layers = number_of_layers_in_bank(best_base_elevation)
    set_water_force(iteration, int_number_of_layers, bank_geom_x, bank_geom_z, base_station, best_base_elevation, water_elevation, water_bank_intersect_station, confining_force, confining_angle)
    set_floodplain_shear_intersect(iteration, bank_geom_x, bank_geom_z, base_station, best_base_elevation, best_failure_angle, fp_intersect_station, fp_intersect_elevation)
    set_layer_weight(iteration, int_number_of_layers, bank_geom_x, bank_geom_z, base_station, best_base_elevation, fp_intersect_station, fp_intersect_elevation, weight)


def compute_layer_slice_area(adblBankGeomX, adblBankGeomZ, intToePoint, bankLayerThickNess, boolTension = True, dblMaxTensionCrackDepth = 1.655, channelFlowParams = [130, 0.000025, 1.5, 720]):
    strCantilever = ""
    strCell = ""
    strErrMsg1 = "The minimum factor of safety does not occur at the location and angle that you have specified. Do you want to use the inputted location and angle?"
    strErrMsg2 = "Cannot detect an undercut bank. Please check the geometry and the failure type."
    strErrMsg3 = "The prescribed failure plane angle ({:.1f} degrees) is too steep for this type of failure. The angle has been automatically reduced to {:.1f} degrees."
    strErrMsg4 = "The model has failed to converge. Please try a smaller failure plane angle or choose to not insert a tension crack."
    strErrMsg5 = "Sorry, but no tension crack has been detected for the entered model parameters."
    strErrMsg6 = "Remember to rerun the Set Bank Geometry Macro on INPUT GEOMETRY if you make any changes to the values on this sheet."

    strInputMsg = ""
    strTensionCrack = "Do you want to insert a tension crack in your bank?"
    WAVFile = ""

    intIteration = 0
    dblBaseStation = 0
    dblFPIntersectStation = 0.0
    dblFPIntersectElevation = 0.0
    dblHLengthFailurePlane = 0.0
    intNumberofLayers = 0

    adblConfiningForce = np.zeros(cintNumberofLayers)
    adblConfiningAngle = np.zeros(cintNumberofLayers)
    adblCprimeL = np.zeros(cintNumberofSlices)
    adblPoreWaterForce = np.zeros(cintNumberofSlices)
    adblNormalForce = np.zeros(cintNumberofSlices)
    adblWeight = np.zeros(cintNumberofSlices)
    adbl_x = np.zeros(cintMaxNumberofPoints)
    adbl_z = np.zeros(cintMaxNumberofPoints)
    adblIntersliceNormalForce = np.zeros(cintNumberofSlices)
    adblIntersliceShearForce = np.zeros(cintNumberofSlices)
    adblStation = np.zeros(cintNumberofSlices)
    adblTanPhiPrime = np.zeros(cintNumberofSlices)
    adblWeight = np.zeros(cintNumberofSlices)

    # ReadBankGeometry(adblBankGeomX, adblBankGeomZ, intToePoint)

    # Set the correct output locations depending on whether auto geometry or manual geometry
    # input_geometry_sheet = openpyxl.load_workbook('Input Geometry.xlsx')['Input Geometry']
    # calculations_sheet = openpyxl.load_workbook('Calculations.xlsx')['Calculations']

    if input_geometry_sheet.cell(row=109, column=3).value == 1:
        intOutputColumn = 5
        intOutputRow = 46
    else:
        intOutputColumn = 7
        intOutputRow = 28
        
    # Activate the "Calculations" worksheet
    # (In openpyxl, no need to activate as we access cells directly)

    # Store the inputted base elevation and failure plane angle
    dblBaseElevation = floatv(input_geometry_sheet.cell(row=138, column=5).value) + 0.000001
    dblFailureAngle = floatv(input_geometry_sheet.cell(row=140, column=5).value) * math.pi / 180
    dblWaterElevation = floatv(calculations_sheet.cell(row=63, column=2).value)
    dblWaterBankIntersectStation = float(calculations_sheet.cell(row=31, column=16).value)
    dblBestFoS = 99999999

    # Check whether the bank is undercut
    intUndercut, intUndercutToe, dblMaxUndercut = set_undercut_index(adblBankGeomX, adblBankGeomZ)

    # Check if the auto shear angle option has been selected
    # if (input_geometry_sheet.cell(row=intOutputRow, column=intOutputColumn).value == "" or (intOutputColumn == 5 and input_geometry_sheet.cell(row=44, column=intOutputColumn).value == "")):
    if (True):
        # If the bank is not undercut set the lower limit for the search algorithm equal
        # to 2 points from the end
        if dblMaxUndercut == 0:
            intUndercutToe = cintMaxNumberofPoints - 2

        #! reset base elevation
        dblBaseElevation = 0.000001
        dblFailureAngle = 0

        # Loop over potential failure base locations
        intIteration = 1

        # Evaluate the minimum factor of safety
        compute_minimum_fos(intIteration, intNumberofLayers, adblBankGeomX, adblBankGeomZ, dblBaseStation, dblBaseElevation, dblFailureAngle, dblFPIntersectStation, dblFPIntersectElevation, intUndercutToe, dblWaterElevation, dblWaterBankIntersectStation, adblConfiningForce, adblConfiningAngle, adblWeight, dblBestFoS, intOutputRow, intOutputColumn)
    else:
        # Compute Factor of Safety for the inputted base elevation and failure plane angle
        input_geometry_sheet.cell(row=intOutputRow, column=intOutputColumn).value = dblFailureAngle * 180 / math.pi

        # Calculate intersect of failure surface and bank face
        dblBaseStation = set_bank_shear_intersect_station(intIteration, adblBankGeomX, adblBankGeomZ, dblBaseElevation, dblBaseStation, intOutputRow, intOutputColumn)

        # Calculate intersect of failure surface and floodplain
        dblFPIntersectStation, dblFPIntersectElevation = set_floodplain_shear_intersect(intIteration, adblBankGeomX, adblBankGeomZ, dblBaseStation, dblBaseElevation, dblFailureAngle, dblFPIntersectStation, dblFPIntersectElevation)

        # Determine how many layers span the failure block
        intNumberofLayers = number_of_layers_in_bank(dblBaseElevation)

        # xcel_fx.cells_reset()

        adblConfiningForce, adblConfiningAngle = set_water_force(intIteration, intNumberofLayers, adblBankGeomX, adblBankGeomZ,dblBaseStation, dblBaseElevation, dblWaterElevation, dblWaterBankIntersectStation, adblConfiningForce, adblConfiningAngle)

        # Calculate areas of the layers
        adblWeight = set_layer_weight(intIteration, intNumberofLayers, adblBankGeomX, adblBankGeomZ,
                    dblBaseStation, dblBaseElevation, dblFPIntersectStation,
                    dblFPIntersectElevation, adblWeight)
    
    if (boolTension):
        # 确定Failure的层数
        # dblBaseElevation = float(input_geometry_sheet.cell(row=140, column=5).value)
        intNumberofLayers = number_of_layers_in_bank(dblBaseElevation)

        min_angle = min(float(calculations_sheet.cell(row=row, column=4).value) for row in range(9, 9 + intNumberofLayers))
        if float(input_geometry_sheet.cell(row=140, column=5).value) > 45 + min_angle:
            print("Caution: " + strErrMsg3)
            
            # 更新失败平面角度
            if input_geometry_sheet.cell(row=109, column=3).value == 1:
                input_geometry_sheet.cell(row=intOutputRow, column=intOutputColumn).value = 44.99 + 0.5 * min_angle
            else:
                input_geometry_sheet.cell(row=intOutputRow, column=intOutputColumn).value = 44.99 + 0.5 * min_angle

            
            xcel_fx.cells_reset()
            
            # 设置初始河岸几何
            dblFailureAngle = input_geometry_sheet.cell(row=140, column=5).value * math.pi / 180
            set_bank_shear_intersect_station(intIteration, adblBankGeomX, adblBankGeomZ, dblBaseElevation, dblBaseStation, intOutputRow, intOutputColumn)
            set_floodplain_shear_intersect(intIteration, adblBankGeomX, adblBankGeomZ, dblBaseStation, dblBaseElevation, dblFailureAngle, dblFPIntersectStation, dblFPIntersectElevation)

            # 重新计算约束力和角度
            xcel_fx.cells_reset()
            adblConfiningForce, adblConfiningAngle = set_water_force(intIteration, intNumberofLayers, adblBankGeomX, adblBankGeomZ, dblBaseStation, dblBaseElevation, dblWaterElevation, dblWaterBankIntersectStation, adblConfiningForce, adblConfiningAngle)

            # 重新计算各层的面积
            set_layer_weight(intIteration, intNumberofLayers, adblBankGeomX, adblBankGeomZ, dblBaseStation, dblBaseElevation, dblFPIntersectStation, dblFPIntersectElevation, adblWeight)
    
        for row in range(4, 19):  # 从第4行到第18行
            for col in range(4, 10):  # 从第4列到第9列
                vert_slice_calcs_sheet.cell(row=row, column=col).value = None
        # for row in vert_slice_calcs_sheet.iter_rows(min_row=4, max_row=18, min_col=4, max_col=9):
        #     for cell in row:
        #         cell.value = None
        
        int_number_of_slices = cintNumberofLayers * (cintNumberofSlices // cintNumberofLayers)
        dbl_top_station = dblBaseStation
        dbl_top_elevation = dblBaseElevation
        dbl_bottom_elevation = dbl_top_elevation
        vert_slice_calcs_sheet.cell(row=int_number_of_slices + 32, column=16).value = dbl_top_station
        vert_slice_calcs_sheet.cell(row=int_number_of_slices + 5, column=17).value = dbl_top_elevation
        vert_slice_calcs_sheet.cell(row=int_number_of_slices + 32, column=17).value = dbl_bottom_elevation

        xcel_fx.cells_reset()
        
        for int_slice in range(int_number_of_slices - 1, 0, -1):
            int_sub_slice = 1 + int_slice % (cintNumberofSlices // cintNumberofLayers)
            int_layer = round((int_slice + 2) / (cintNumberofSlices // cintNumberofLayers))
            dbl_top_station = dbl_top_station - (dbl_top_station - floatv(calculations_sheet.cell(row=21 + int_layer, column=16).value)) / int_sub_slice
            if dblMaxUndercut > 0 and dbl_top_station > adblBankGeomX[intUndercutToe]:
                dbl_top_station = adblBankGeomX[intUndercutToe]
            
            dbl_bottom_elevation = (float(calculations_sheet.cell(row=21 + int_layer, column=17).value) -
                                    (float(calculations_sheet.cell(row=21 + int_layer, column=17).value) -
                                    float(vert_slice_calcs_sheet.cell(row=int_slice + 33, column=17).value)) *
                                    (dbl_top_station - floatv(calculations_sheet.cell(row=21 + int_layer, column=16).value)) /
                                    (floatv(vert_slice_calcs_sheet.cell(row=int_slice + 33, column=16).value) - 
                                    floatv(calculations_sheet.cell(row=21 + int_layer, column=16).value)))
            
            int_point = 0
            while cintMaxNumberofPoints > int_point + 1:
                dbl_station1 = adblBankGeomX[int_point]
                dbl_station2 = adblBankGeomX[int_point + 1]
                if dbl_station2 > dbl_top_station:
                    break
                int_point += 1
            dbl_elevation1 = adblBankGeomZ[int_point]
            dbl_elevation2 = adblBankGeomZ[int_point + 1]
            
            dbl_top_elevation = dbl_elevation2 - (dbl_elevation2 - dbl_elevation1) * (dbl_top_station - dbl_station2) / (dbl_station1 - dbl_station2)
            vert_slice_calcs_sheet.cell(row=int_slice + 32, column=16).value = dbl_top_station
            vert_slice_calcs_sheet.cell(row=int_slice + 5, column=17).value = dbl_top_elevation
            vert_slice_calcs_sheet.cell(row=int_slice + 32, column=17).value = dbl_bottom_elevation
            xcel_fx.cells_reset()
        
        for int_slice in range(int_number_of_slices + 1, cintNumberofSlices + 1):
            vert_slice_calcs_sheet.cell(row=int_slice + 5, column=17).value = ""
            vert_slice_calcs_sheet.cell(row=int_slice + 32, column=16).value = 0
            vert_slice_calcs_sheet.cell(row=int_slice + 32, column=17).value = -99999

        xcel_fx.cells_reset()
        
        for int_slice in range(1, int_number_of_slices + 1):
            int_number_of_layers = round((int_slice + 1) / (cintNumberofSlices // cintNumberofLayers))
            int_first_layer = int_number_of_layers
            while int_first_layer > 1 and max(float(vert_slice_calcs_sheet.cell(row=int_slice + 4, column=17).value),  float(vert_slice_calcs_sheet.cell(row=int_slice + 5, column=17).value)) >  float(calculations_sheet.cell(row=4 + int_first_layer, column=17).value):
                int_first_layer -= 1
            int_sub_slice = int_slice - (int_number_of_layers - 1) * (cintNumberofSlices // cintNumberofLayers)
            
            for int_layer in range(int_number_of_layers, int_first_layer - 1, -1):
                int_vertex = -1
                if int_layer == int_number_of_layers and int_sub_slice == 1:
                    adbl_x[int_vertex + 1] = vert_slice_calcs_sheet.cell(row=32 + int_slice, column=16).value
                    adbl_z[int_vertex + 1] = vert_slice_calcs_sheet.cell(row=32 + int_slice, column=17).value
                    int_vertex += 1
                elif int_layer == int_number_of_layers:
                    adbl_x[int_vertex + 1] = vert_slice_calcs_sheet.cell(row=32 + int_slice, column=16).value
                    adbl_z[int_vertex + 1] = vert_slice_calcs_sheet.cell(row=32 + int_slice, column=17).value
                    adbl_x[int_vertex + 2] = vert_slice_calcs_sheet.cell(row=31 + int_slice, column=16).value
                    adbl_z[int_vertex + 2] = vert_slice_calcs_sheet.cell(row=31 + int_slice, column=17).value
                    int_vertex += 2
                else:
                    adbl_x[int_vertex + 1] = dbl_station_top_right
                    adbl_z[int_vertex + 1] = dbl_elevation_top_right
                    adbl_x[int_vertex + 2] = dbl_station_top_left
                    adbl_z[int_vertex + 2] = dbl_elevation_top_left
                    int_vertex += 2
                
                if int_layer == int_number_of_layers and int_sub_slice == 1:
                    dbl_station_top_left = float(vert_slice_calcs_sheet.cell(row=31 + int_slice, column=16).value)
                    dbl_elevation_top_left = float(vert_slice_calcs_sheet.cell(row=31 + int_slice, column=17).value)
                elif int_layer == int_first_layer:
                    dbl_station_top_left = float(vert_slice_calcs_sheet.cell(row=4 + int_slice, column=16).value)
                    dbl_elevation_top_left = float(vert_slice_calcs_sheet.cell(row=4 + int_slice, column=17).value)
                else:
                    dbl_station_top_left = float(vert_slice_calcs_sheet.cell(row=4 + int_slice, column=16).value)
                    dbl_elevation_top_left = float(calculations_sheet.cell(row=4 + int_layer, column=17).value)
                adbl_x[int_vertex + 1] = dbl_station_top_left
                adbl_z[int_vertex + 1] = dbl_elevation_top_left
                int_vertex += 1
                
                if int_slice == int_number_of_slices:
                    dbl_station_top_right = float(calculations_sheet.cell(row=4 + int_layer, column=16).value)
                else:
                    dbl_station_top_right = min(float(vert_slice_calcs_sheet.cell(row=5 + int_slice, column=16).value), 
                                                float(calculations_sheet.cell(row=4 + int_layer, column=16).value))
                if int_layer == int_first_layer:
                    if int_slice == cintNumberofSlices:
                        dbl_elevation_top_right = float(calculations_sheet.cell(row=5, column=17).value)
                    else:
                        dbl_elevation_top_right = max(float(vert_slice_calcs_sheet.cell(row=5 + int_slice, column=17).value), 
                                                    float(calculations_sheet.cell(row=4 + int_layer, column=17).value))
                else:
                    dbl_elevation_top_right = float(calculations_sheet.cell(row=4 + int_layer, column=17).value)
                
                if float(calculations_sheet.cell(row=4 + int_layer, column=16).value) > float(vert_slice_calcs_sheet.cell(row=4 + int_slice, column=16).value):
                    adbl_x[int_vertex + 1] = dbl_station_top_right
                    adbl_z[int_vertex + 1] = dbl_elevation_top_right
                    int_vertex += 1
                
                for int_point in range(0, cintMaxNumberofPoints):
                    if ((int_slice == int_number_of_slices or adbl_x[0] > adblBankGeomX[int_point]) and 
                        dbl_elevation_top_right > adblBankGeomZ[int_point] and 
                        adblBankGeomZ[int_point] > adbl_z[0]):
                        adbl_x[int_vertex + 1] = adblBankGeomX[int_point]
                        adbl_z[int_vertex + 1] = adblBankGeomZ[int_point]
                        int_vertex += 1
                
                if (float(vert_slice_calcs_sheet.cell(row=5 + int_slice, column=16).value) > float(calculations_sheet.cell(row=4 + int_layer, column=16).value) and 
                    float(vert_slice_calcs_sheet.cell(row=5 + int_slice, column=17).value) > adbl_z[0]):
                    adbl_x[int_vertex + 1] = float(vert_slice_calcs_sheet.cell(row=5 + int_slice, column=16).value)
                    adbl_z[int_vertex + 1] = float(vert_slice_calcs_sheet.cell(row=5 + int_slice, column=17).value)
                    int_vertex += 1
                
                dbl_area = polygon_area(adbl_x, adbl_z, int_vertex + 1)
                vert_slice_calcs_sheet.cell(row=3 + int_slice, column=3 + int_layer).value = dbl_area
        # 初始化变量
        int_slice = 1
        bln_bankfull = False

        xcel_fx.cells_reset()

        dbl_top_elevation = round(vert_slice_calcs_sheet.cell(row=5 + int_slice, column=17).value, 6)
        while dbl_top_elevation > dblWaterElevation:
            dbl_top_elevation = round(vert_slice_calcs_sheet.cell(row=5 + int_slice, column=17).value, 6)
            int_slice += 1
            if cintNumberofSlices == int_slice:
                dbl_top_elevation = round(vert_slice_calcs_sheet.cell(row=5, column=17).value, 6)
                break

        # 重新计算Bank Intersect Station如果是bankfull
        if bln_bankfull:
            dbl_water_bank_intersect_station = calculations_sheet.cell(row=16, column=16).value

        # 初始化两个顶点
        dbl_station_bottom_right = float(vert_slice_calcs_sheet.cell(row=4 + int_slice, column=16).value)
        dbl_elevation_bottom_right = float(vert_slice_calcs_sheet.cell(row=4 + int_slice, column=17).value)
        dbl_station_top_right = float(vert_slice_calcs_sheet.cell(row=4 + int_slice, column=16).value)
        dbl_elevation_top_right = dblWaterElevation

        # 循环遍历切片
        bln_first_slice = False
        for int_slice in range(1, cintNumberofSlices + 1):
            dbl_top_elevation = round(vert_slice_calcs_sheet.cell(row=5 + int_slice, column=17).value, 6)
            if dblWaterElevation >= dbl_top_elevation:
                if not bln_first_slice:
                    int_first_slice = int_slice
                    bln_first_slice = True

                # 顶部谷侧交点为上一个切片的底部谷侧交点
                dbl_station_top_left = dbl_station_top_right
                dbl_elevation_top_left = dbl_elevation_top_right

                # 组装切片中的水体体积的多边形顶点
                int_vertex = -1
                if int_slice == int_first_slice and not bln_bankfull:
                    # 仅一个顶点：水面与bank face的交点
                    adbl_x[int_vertex + 1] = dblWaterBankIntersectStation
                    adbl_z[int_vertex + 1] = dblWaterElevation
                    int_vertex += 1
                else:
                    # 两个顶点谷侧，顶部然后底部
                    adbl_x[int_vertex + 1] = dbl_station_bottom_right
                    adbl_z[int_vertex + 1] = dbl_elevation_bottom_right
                    adbl_x[int_vertex + 2] = dbl_station_top_left
                    adbl_z[int_vertex + 2] = dblWaterElevation
                    int_vertex += 2

                # 顶部stream侧顶点
                if int_slice == cintNumberofSlices:
                    dbl_station_top_right = max(float(vert_slice_calcs_sheet.cell(row=5 + int_slice, column=16).value), dblWaterBankIntersectStation)
                else:
                    dbl_station_top_right = vert_slice_calcs_sheet.cell(row=5 + int_slice, column=16).value
                dbl_elevation_top_right = dblWaterElevation
                adbl_x[int_vertex + 1] = dbl_station_top_right
                adbl_z[int_vertex + 1] = dbl_elevation_top_right
                int_vertex += 1

                # 底部stream侧顶点
                dbl_station_bottom_right = dbl_station_top_right
                dbl_elevation_bottom_right = vert_slice_calcs_sheet.cell(row=5 + int_slice, column=17).value
                adbl_x[int_vertex + 1] = dbl_station_bottom_right
                adbl_z[int_vertex + 1] = dbl_elevation_bottom_right
                int_vertex += 1

                # 查找可能添加到多边形的第一个bank face节点
                for int_point in range(cintMaxNumberofPoints - 1, 0, -1):
                    if adblBankGeomZ[int_point] > vert_slice_calcs_sheet.cell(row=5 + int_slice, column=17).value:
                        break

                # 添加bank节点到多边形，直到节点的高程等于或低于soil slice的底部
                # while adbl_z[1] > float(vert_slice_calcs_sheet.cell(row=int_point, column=17).value) and float(vert_slice_calcs_sheet.cell(row=int_point, column=16).value) > float(vert_slice_calcs_sheet.cell(row=4 + int_slice, column=16).value):
                tCount = 0
                while adbl_z[1] > adblBankGeomZ[int_point] and adblBankGeomX[int_point] > float(vert_slice_calcs_sheet.cell(4 + int_slice, column=16).value):
                    adbl_x[int_vertex + 1] = adblBankGeomX[int_point]
                    adbl_z[int_vertex + 1] = adblBankGeomZ[int_point]
                    int_vertex += 1
                    int_point -= 1
                    tCount += 1

                # 计算体积并写入电子表格
                dbl_area = polygon_area(adbl_x, adbl_z, int_vertex)
                vert_slice_calcs_sheet.cell(row=3 + int_slice, column=9).value = dbl_area

            else:
                vert_slice_calcs_sheet.cell(row=3 + int_slice, column=9).value = ""

        for int_slice in range(int_slice + 1, cintNumberofSlices + 1):
            vert_slice_calcs_sheet.cell(row=3 + int_slice, column=9).value = ""

        # 计算约束力
        if dblWaterElevation <= dblBaseElevation:
            for int_slice in range(1, cintNumberofSlices + 1):
                vert_slice_calcs_sheet.cell(row=61, column=1 + int_slice).value = 0
        else:
            vert_slice_calcs_sheet.cell(row=61, column=1 + int_slice).value = 0.5 * 9.807 * ((dblWaterElevation - dblBaseElevation) ** 2)
            for int_slice in range(1, int_slice):
                vert_slice_calcs_sheet.cell(row=61, column=1 + int_slice).value = 0
            for int_slice in range(int_slice + 1, cintNumberofSlices + 1):
                vert_slice_calcs_sheet.cell(row=61, column=1 + int_slice).value = 0
        
        xcel_fx.cells_reset()

        # 确定failure plane的水平长度
        dbl_fp_intersect_station = 0  # 根据实际情况设置
        dbl_h_length_failure_plane = calculations_sheet.cell(row=15, column=16).value - dbl_fp_intersect_station

        # 激活"VertSliceCalcs"工作表
        # vert_slice_calcs_sheet.activate()
        adblConfiningForce[0] = float(vert_slice_calcs_sheet.cell(row=61, column=17).value)

        # 确定有多少切片跨越失败块
        int_number_of_slices = 0
        for int_slice in range(1, cintNumberofSlices + 1):
            dbl_top_elevation = float(vert_slice_calcs_sheet.cell(row=31 + int_slice, column=17).value)
            if dbl_top_elevation <= dblBaseElevation:
                break
            else:
                int_number_of_slices += 1

        dblFoS2 = math.cos(dblFailureAngle) * (float(vert_slice_calcs_sheet.cell(55, 4).value) +
                                        float(vert_slice_calcs_sheet.cell(62, 17).value) -
                                        float(vert_slice_calcs_sheet.cell(60, 17).value)) / (
            float(vert_slice_calcs_sheet.cell(64, 17).value) - adblConfiningForce[0])
        intFirstSlice = 1

        # 开始迭代
        intIteration = 0
        dblFoS1 = 0

        while round(dblFoS1, 2) != round(dblFoS2, 2) or intIteration < 2:
            dblFoS1 = dblFoS2
            intIteration += 1

            if intIteration == 2:
                dblTemp = float('inf')
                for intLayer in range(1, intNumberofLayers + 1):
                    value = float(calculations_sheet.cell(23 + intLayer, 4).value)
                    if dblTemp > value:
                        dblTemp = value

                max_bank_output = max(float(bank_model_output_sheet.cell(84, 8).value),
                                    float(bank_model_output_sheet.cell(85, 8).value),
                                    float(bank_model_output_sheet.cell(86, 8).value),
                                    float(bank_model_output_sheet.cell(87, 8).value),
                                    float(bank_model_output_sheet.cell(88, 8).value))

                dblLohnesHandy = round((2 * max_bank_output / dblTemp) * math.tan(math.pi / 4 + (max(float(calculations_sheet.cell(9, 4).value),  float(calculations_sheet.cell(10, 4).value),float(calculations_sheet.cell(11, 4).value),float(calculations_sheet.cell(12, 4).value),float(calculations_sheet.cell(13, 4).value))) * math.pi / 360), 2)

                # # 请求用户输入最大张力裂缝深度
                # strInputMsg = f"Enter the Tension Crack Depth. For these soils, the maximum tension crack depth according to Lohnes and Handy (1968) is {dblLohnesHandy} m. A better estimate can often be obtained from the heights of vertical faces observed in the field."
                # dblMaxTensionCrackDepth = float(input(strInputMsg))  # 模拟输入框

                # 确定张力裂缝的位置
                for intSlice in range(int_number_of_slices, 0, -1):
                    if (0 > adblIntersliceNormalForce[intSlice - 1]) and (dblMaxTensionCrackDepth >= (float(vert_slice_calcs_sheet.cell(5, 17).value) - float(vert_slice_calcs_sheet.cell(32 + intSlice, 17).value))):
                        dblFPIntersectStation = adblStation[intSlice]
                        dblHLengthFailurePlane = calculations_sheet.cell(15, 16).value - dblFPIntersectStation
                        vert_slice_calcs_sheet.cell(26, 16).value = dblFPIntersectStation
                        vert_slice_calcs_sheet.cell(26, 17).value = vert_slice_calcs_sheet.cell(32 + intSlice, 17).value
                        vert_slice_calcs_sheet.cell(27, 16).value = dblFPIntersectStation
                        vert_slice_calcs_sheet.cell(27, 17).value = vert_slice_calcs_sheet.cell(5 + intSlice, 17).value
                        intFirstSlice = intSlice + 1
                        intRow = 3 + (intFirstSlice - 1)
                        while intRow > 3:
                            vert_slice_calcs_sheet.cell(intRow, 4).value = ""
                            vert_slice_calcs_sheet.cell(intRow, 5).value = ""
                            vert_slice_calcs_sheet.cell(intRow, 6).value = ""
                            vert_slice_calcs_sheet.cell(intRow, 7).value = ""
                            vert_slice_calcs_sheet.cell(intRow, 8).value = ""
                            vert_slice_calcs_sheet.cell(intRow, 9).value = ""
                            intRow -= 1
                        break
            else:
                intSlice = intFirstSlice

            # 初始化抗力和驱动力
            dblSumResistingForces = 0
            dblSumDrivingForces = 0

            # 初始化片间法向力和剪切力
            adblIntersliceNormalForce[intFirstSlice - 1] = 0
            adblIntersliceShearForce[intFirstSlice - 1] = 0
            
            xcel_fx.cells_reset()

            for intSlice in range(intFirstSlice, int_number_of_slices + 1):
                if intIteration == 1:
                    adblStation[intSlice - 1] = float(vert_slice_calcs_sheet.cell(5 + intSlice, 16).value)
                    adblWeight[intSlice - 1] = float(vert_slice_calcs_sheet.cell(3 + intSlice, 10).value)
                    adblCprimeL[intSlice - 1] = float(vert_slice_calcs_sheet.cell(39 + intSlice, 4).value)
                    adblPoreWaterForce[intSlice - 1] = float(vert_slice_calcs_sheet.cell(60, 1 + intSlice).value)
                    adblNormalForce[intSlice - 1] = adblWeight[intSlice - 1] * math.cos(dblFailureAngle)
                    adblTanPhiPrime[intSlice - 1] = math.tan(float(calculations_sheet.cell(8 + math.ceil(intSlice / 3), 4).value) * math.pi / 180)
                    adblIntersliceShearForce[intSlice - 1] = 0

                if intSlice == int_number_of_slices:
                    adblIntersliceNormalForce[intSlice - 1] = 0
                else:
                    adblIntersliceNormalForce[intSlice - 1] = adblIntersliceNormalForce[intSlice - 1] - ((adblCprimeL[intSlice - 1] - adblPoreWaterForce[intSlice - 1]) * math.cos(dblFailureAngle) / dblFoS1) + adblNormalForce[intSlice - 1] * (math.sin(dblFailureAngle) - (math.cos(dblFailureAngle) * adblTanPhiPrime[intSlice - 1] / dblFoS1))

                #! RuntimeWarning: invalid value encountered in double_scalars
                if dblHLengthFailurePlane == 0.0:
                    dblHLengthFailurePlane = 1
                if intIteration != 1:
                    adblIntersliceShearForce[intSlice - 1] = 0.4 * adblIntersliceNormalForce[intSlice - 1] * math.sin(math.pi * (adblStation[intSlice - 1] - dblFPIntersectStation) / dblHLengthFailurePlane)

                adblNormalForce[intSlice - 1] = (adblWeight[intSlice - 1] + (adblIntersliceShearForce[intSlice - 1] - adblIntersliceShearForce[intSlice - 1]) - ((adblCprimeL[intSlice - 1] - adblPoreWaterForce[intSlice - 1]) * math.sin(dblFailureAngle) / dblFoS1)) / (math.cos(dblFailureAngle) + (adblTanPhiPrime[intSlice - 1] * math.sin(dblFailureAngle) / dblFoS1))
                if adblNormalForce[intSlice - 1] < 0:
                    adblNormalForce[intSlice - 1] = 0

                #！bug mark in 7-22
                dblSumResistingForces += adblNormalForce[intSlice - 1] * adblTanPhiPrime[intSlice - 1] + adblCprimeL[intSlice - 1] - adblPoreWaterForce[intSlice - 1]
                dblSumDrivingForces += adblNormalForce[intSlice - 1]

            if dblSumDrivingForces == 0:
                dblSumDrivingForces = 1

            dblFoS2 = (math.cos(dblFailureAngle) * dblSumResistingForces + dblFoS1 * adblConfiningForce[1]) / (math.sin(dblFailureAngle) * dblSumDrivingForces)

            if intIteration == 32767:
                raise Exception("Error! Check that the failure plane angle is not too steep")
            # print(calculations_sheet.cell(77, 12).value)

        xcel_fx.cells_reset()
        if intIteration == 1:
            print("No Tension Crack!")
        vert_slice_calcs_sheet.cell(67, 17).value = (dblFoS1 + dblFoS2) / 2
    return calculations_sheet.cell(77, 12).value, vert_slice_calcs_sheet.cell(67, 17).value, input_geometry_sheet.cell(44, 5).value, input_geometry_sheet.cell(46, 5).value, calculations_sheet.cell(15, 16).value, calculations_sheet.cell(15, 17).value, calculations_sheet.cell(16, 16).value, calculations_sheet.cell(16, 17).value

    # 保存Excel文件
    # wb.save('你的Excel文件.xlsx')

    # # 激活所需的工作表并显示信息
    # if dblFoS1 != 0:
    #     print(f"The Fs with no tension crack is {round(calculations_sheet.cell(77, 12).value, 2)}")
    #     print("Reminder.")
    # print("123")