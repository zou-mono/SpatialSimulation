+ Gv.Weight_neccessary不仅影响frmModelCal中Weight表的显示顺序，
而且控制了模型中TOPSIS矩阵运算的顺序；如果改动了这个变量要同时改动 
SCIPCal.py中model_feasibles函数内部的sol_list元素顺序