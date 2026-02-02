'''
Date: 2024/06/07
Author: Fengyuan Zhang
Email: franklinzhang@foxmail.com
Description: Test file
'''
from BSTEM_xls import set_bank_geometry, initVX, compute_layer_slice_area, view_bank
import Excel_source_codes.xcel_fx as xcel_fx

# Call the function
x_values = [0.00,24.39,28.62,32.69,36.76,39.15,41.55,45.84,50.13,51.10,52.78,56.79,60.81,64.83,68.85,72.86,73.67,77.68,84.45,91.65,98.49,102.88,109.54]
z_values = [3.43,3.43,1.14,-1.46,-4.07,-4.07,-5.24,-7.41,-9.58,-11.57,-15.01,-17.72,-20.43,-23.14,-25.85,-28.56,-29.10,-29.10,-29.10,-29.10,-29.10,-29.10,-29.10]

x_values2 = [0.00,10.59,10.59,15.44,20.30,25.15,30.00,34.85,39.70,44.55,49.41,54.26,59.11,63.96,68.81,73.67,73.67,77.68,84.45,91.65,98.49,102.88,109.54]
z_values2 = [3.43,3.43,2.93,0.47,-2.00,-4.46,-6.93,-9.39,-11.85,-14.32,-16.78,-19.24,-21.71,-24.17,-26.64,-29.10,-29.10,-29.10,-29.10,-29.10,-29.10,-29.10,-29.10]
#result: fos = 0.87
x_values3 = [0.00,24.39,26.68,29.28,31.89,31.89,33.06,35.23,37.40,39.39,42.83,45.54,48.25,50.96,53.67,56.38,56.92,77.68,84.45,91.65,98.49,102.88,109.54]
z_values3 = [3.43,3.43,1.14,-1.46,-4.07,-4.07,-5.24,-7.41,-9.58,-11.57,-15.01,-17.72,-20.43,-23.14,-25.85,-28.56,-29.10,-29.10,-29.10,-29.10,-29.10,-29.10,-29.10]
#result: fos = 1.21
x_values4 = [0.00,24.39,27.82,31.73,35.64,35.64,37.40,40.65,43.91,46.89,52.05,56.11,60.18,64.24,68.31,72.37,73.18,77.68,84.45,91.65,98.49,102.88,109.54]
z_values4 = [3.43,3.43,1.14,-1.46,-4.07,-4.07,-5.24,-7.41,-9.58,-11.57,-15.01,-17.72,-20.43,-23.14,-25.85,-28.56,-29.10,-29.10,-29.10,-29.10,-29.10,-29.10,-29.10]
#result: fos = 2.5
x_values5 = [0.00,24.39,31.25,39.06,46.89,46.89,50.41,56.92,63.42,69.39,79.71,87.84,95.97,104.10,112.23,120.36,121.98,123.00,125.00,127.00,129.00,131.00,133.00]
z_values5 = [3.43,3.43,1.14,-1.46,-4.07,-4.07,-5.24,-7.41,-9.58,-11.57,-15.01,-17.72,-20.43,-23.14,-25.85,-28.56,-29.10,-29.10,-29.10,-29.10,-29.10,-29.10,-29.10]
#result: fos = 1.71
x_values6 = [0.00,24.39,28.96,34.17,39.39,39.39,41.74,46.07,50.41,54.39,61.27,66.69,72.11,77.53,82.95,88.37,89.45,92.00,94.00,96.00,98.49,102.88,109.54]
z_values6 = [3.43,3.43,1.14,-1.46,-4.07,-4.07,-5.24,-7.41,-9.58,-11.57,-15.01,-17.72,-20.43,-23.14,-25.85,-28.56,-29.10,-29.10,-29.10,-29.10,-29.10,-29.10,-29.10]
intToePoint = 17

bankLayerThickNess = [1.5, 6, 7.5, 15, 10]
channelFlowParams = [130, 0.000025, 1.5, 720]
# 
list_own_friction_angle = [8.9, 29.0, 5.6, 29.4, 29.4]

# view_bank(x_values, z_values)
# initVX("./Excel_source_codes/xl/worksheets/")
initVX('/Users/soku/Desktop/bank_model_service/BankModel_Service/model/erosionModel/Excel_source_codes/worksheets/')
# set_bank_geometry(x_values, z_values, intToePoint)
# view_bank(x_values3, z_values3)
set_bank_geometry(x_values3, z_values3, intToePoint)
xcel_fx.cells_reset()
# compute_layer_slice_area(x_values, z_values, intToePoint, bankLayerThickNess, -29.1, 26.92, 130, 0.0000255, 1.5, 720, list_own_friction_angle = list_own_friction_angle, list_own_list_own_phi_b = list_own_list_own_phi_b)
fos, fs, seEle, ssAngle, fX1, fZ1, fX2, fZ2 = compute_layer_slice_area(x_values3, z_values3, intToePoint, bankLayerThickNess = bankLayerThickNess, boolTension = False, channelFlowParams = channelFlowParams)
print(fos)
print(fs)
print(seEle)
print(ssAngle)
print(fX1)
print(fZ1)
print(fX2)
print(fZ2)

# print("finished!")