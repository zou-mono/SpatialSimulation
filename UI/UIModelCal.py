# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'UIModelCal.ui'
#
# Created by: PyQt5 UI code generator 5.15.9
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_frmModelCal(object):
    def setupUi(self, frmModelCal):
        frmModelCal.setObjectName("frmModelCal")
        frmModelCal.resize(516, 572)
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout(frmModelCal)
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.scrollArea = QtWidgets.QScrollArea(frmModelCal)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(250)
        sizePolicy.setHeightForWidth(self.scrollArea.sizePolicy().hasHeightForWidth())
        self.scrollArea.setSizePolicy(sizePolicy)
        self.scrollArea.setFrameShape(QtWidgets.QFrame.WinPanel)
        self.scrollArea.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        self.scrollArea.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setObjectName("scrollArea")
        self.scrollAreaWidgetContents = QtWidgets.QWidget()
        self.scrollAreaWidgetContents.setGeometry(QtCore.QRect(0, 0, 477, 990))
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.scrollAreaWidgetContents.sizePolicy().hasHeightForWidth())
        self.scrollAreaWidgetContents.setSizePolicy(sizePolicy)
        self.scrollAreaWidgetContents.setObjectName("scrollAreaWidgetContents")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.scrollAreaWidgetContents)
        self.verticalLayout.setObjectName("verticalLayout")
        self.verticalLayout_7 = QtWidgets.QVBoxLayout()
        self.verticalLayout_7.setObjectName("verticalLayout_7")
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.label_9 = QtWidgets.QLabel(self.scrollAreaWidgetContents)
        font = QtGui.QFont()
        font.setFamily("微软雅黑")
        font.setPointSize(10)
        font.setBold(True)
        font.setWeight(75)
        self.label_9.setFont(font)
        self.label_9.setObjectName("label_9")
        self.horizontalLayout.addWidget(self.label_9)
        self.txt_model_name = QtWidgets.QLineEdit(self.scrollAreaWidgetContents)
        self.txt_model_name.setObjectName("txt_model_name")
        self.horizontalLayout.addWidget(self.txt_model_name)
        self.verticalLayout_7.addLayout(self.horizontalLayout)
        spacerItem = QtWidgets.QSpacerItem(20, 5, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Fixed)
        self.verticalLayout_7.addItem(spacerItem)
        self.groupBox3 = QtWidgets.QGroupBox(self.scrollAreaWidgetContents)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.groupBox3.sizePolicy().hasHeightForWidth())
        self.groupBox3.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setFamily("微软雅黑")
        font.setPointSize(10)
        font.setBold(True)
        font.setWeight(75)
        self.groupBox3.setFont(font)
        self.groupBox3.setObjectName("groupBox3")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(self.groupBox3)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.formLayout_2 = QtWidgets.QFormLayout()
        self.formLayout_2.setObjectName("formLayout_2")
        self.label_7 = QtWidgets.QLabel(self.groupBox3)
        font = QtGui.QFont()
        font.setFamily("微软雅黑")
        font.setPointSize(9)
        font.setBold(False)
        font.setWeight(50)
        self.label_7.setFont(font)
        self.label_7.setObjectName("label_7")
        self.formLayout_2.setWidget(0, QtWidgets.QFormLayout.LabelRole, self.label_7)
        self.txt_indicator_xzjjl = QtWidgets.QLineEdit(self.groupBox3)
        font = QtGui.QFont()
        font.setFamily("微软雅黑")
        font.setPointSize(10)
        font.setBold(False)
        font.setWeight(50)
        self.txt_indicator_xzjjl.setFont(font)
        self.txt_indicator_xzjjl.setObjectName("txt_indicator_xzjjl")
        self.formLayout_2.setWidget(0, QtWidgets.QFormLayout.FieldRole, self.txt_indicator_xzjjl)
        self.label_8 = QtWidgets.QLabel(self.groupBox3)
        font = QtGui.QFont()
        font.setFamily("微软雅黑")
        font.setPointSize(9)
        font.setBold(False)
        font.setWeight(50)
        self.label_8.setFont(font)
        self.label_8.setObjectName("label_8")
        self.formLayout_2.setWidget(1, QtWidgets.QFormLayout.LabelRole, self.label_8)
        self.txt_indicator_ccjzl = QtWidgets.QLineEdit(self.groupBox3)
        font = QtGui.QFont()
        font.setFamily("微软雅黑")
        font.setPointSize(10)
        font.setBold(False)
        font.setWeight(50)
        self.txt_indicator_ccjzl.setFont(font)
        self.txt_indicator_ccjzl.setObjectName("txt_indicator_ccjzl")
        self.formLayout_2.setWidget(1, QtWidgets.QFormLayout.FieldRole, self.txt_indicator_ccjzl)
        self.label_10 = QtWidgets.QLabel(self.groupBox3)
        font = QtGui.QFont()
        font.setFamily("微软雅黑")
        font.setPointSize(9)
        font.setBold(False)
        font.setWeight(50)
        self.label_10.setFont(font)
        self.label_10.setObjectName("label_10")
        self.formLayout_2.setWidget(2, QtWidgets.QFormLayout.LabelRole, self.label_10)
        self.txt_indicator_zzphzs = QtWidgets.QLineEdit(self.groupBox3)
        font = QtGui.QFont()
        font.setFamily("微软雅黑")
        font.setPointSize(10)
        font.setBold(False)
        font.setWeight(50)
        self.txt_indicator_zzphzs.setFont(font)
        self.txt_indicator_zzphzs.setObjectName("txt_indicator_zzphzs")
        self.formLayout_2.setWidget(2, QtWidgets.QFormLayout.FieldRole, self.txt_indicator_zzphzs)
        self.label_11 = QtWidgets.QLabel(self.groupBox3)
        font = QtGui.QFont()
        font.setFamily("微软雅黑")
        font.setPointSize(9)
        font.setBold(False)
        font.setWeight(50)
        self.label_11.setFont(font)
        self.label_11.setObjectName("label_11")
        self.formLayout_2.setWidget(3, QtWidgets.QFormLayout.LabelRole, self.label_11)
        self.txt_indicator_jtkdx = QtWidgets.QLineEdit(self.groupBox3)
        font = QtGui.QFont()
        font.setFamily("微软雅黑")
        font.setPointSize(10)
        font.setBold(False)
        font.setWeight(50)
        self.txt_indicator_jtkdx.setFont(font)
        self.txt_indicator_jtkdx.setObjectName("txt_indicator_jtkdx")
        self.formLayout_2.setWidget(3, QtWidgets.QFormLayout.FieldRole, self.txt_indicator_jtkdx)
        self.label_12 = QtWidgets.QLabel(self.groupBox3)
        font = QtGui.QFont()
        font.setFamily("微软雅黑")
        font.setPointSize(9)
        font.setBold(False)
        font.setWeight(50)
        self.label_12.setFont(font)
        self.label_12.setObjectName("label_12")
        self.formLayout_2.setWidget(4, QtWidgets.QFormLayout.LabelRole, self.label_12)
        self.txt_indicator_ggfwsp = QtWidgets.QLineEdit(self.groupBox3)
        font = QtGui.QFont()
        font.setFamily("微软雅黑")
        font.setPointSize(10)
        font.setBold(False)
        font.setWeight(50)
        self.txt_indicator_ggfwsp.setFont(font)
        self.txt_indicator_ggfwsp.setObjectName("txt_indicator_ggfwsp")
        self.formLayout_2.setWidget(4, QtWidgets.QFormLayout.FieldRole, self.txt_indicator_ggfwsp)
        self.verticalLayout_2.addLayout(self.formLayout_2)
        self.verticalLayout_7.addWidget(self.groupBox3)
        self.groupBox2 = QtWidgets.QGroupBox(self.scrollAreaWidgetContents)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.groupBox2.sizePolicy().hasHeightForWidth())
        self.groupBox2.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setFamily("微软雅黑")
        font.setPointSize(10)
        font.setBold(True)
        font.setWeight(75)
        self.groupBox2.setFont(font)
        self.groupBox2.setObjectName("groupBox2")
        self.verticalLayout_6 = QtWidgets.QVBoxLayout(self.groupBox2)
        self.verticalLayout_6.setObjectName("verticalLayout_6")
        self.formLayout = QtWidgets.QFormLayout()
        self.formLayout.setObjectName("formLayout")
        self.label = QtWidgets.QLabel(self.groupBox2)
        font = QtGui.QFont()
        font.setFamily("微软雅黑")
        font.setPointSize(9)
        font.setBold(False)
        font.setWeight(50)
        self.label.setFont(font)
        self.label.setObjectName("label")
        self.formLayout.setWidget(0, QtWidgets.QFormLayout.LabelRole, self.label)
        self.txt_type_csgx = QtWidgets.QLineEdit(self.groupBox2)
        font = QtGui.QFont()
        font.setFamily("微软雅黑")
        font.setPointSize(10)
        font.setBold(False)
        font.setWeight(50)
        self.txt_type_csgx.setFont(font)
        self.txt_type_csgx.setObjectName("txt_type_csgx")
        self.formLayout.setWidget(0, QtWidgets.QFormLayout.FieldRole, self.txt_type_csgx)
        self.label_4 = QtWidgets.QLabel(self.groupBox2)
        font = QtGui.QFont()
        font.setFamily("微软雅黑")
        font.setPointSize(9)
        font.setBold(False)
        font.setWeight(50)
        self.label_4.setFont(font)
        self.label_4.setObjectName("label_4")
        self.formLayout.setWidget(1, QtWidgets.QFormLayout.LabelRole, self.label_4)
        self.txt_type_tdzb = QtWidgets.QLineEdit(self.groupBox2)
        font = QtGui.QFont()
        font.setFamily("微软雅黑")
        font.setPointSize(10)
        font.setBold(False)
        font.setWeight(50)
        self.txt_type_tdzb.setFont(font)
        self.txt_type_tdzb.setObjectName("txt_type_tdzb")
        self.formLayout.setWidget(1, QtWidgets.QFormLayout.FieldRole, self.txt_type_tdzb)
        self.label_5 = QtWidgets.QLabel(self.groupBox2)
        font = QtGui.QFont()
        font.setFamily("微软雅黑")
        font.setPointSize(9)
        font.setBold(False)
        font.setWeight(50)
        self.label_5.setFont(font)
        self.label_5.setObjectName("label_5")
        self.formLayout.setWidget(2, QtWidgets.QFormLayout.LabelRole, self.label_5)
        self.txt_type_zzgjz = QtWidgets.QLineEdit(self.groupBox2)
        font = QtGui.QFont()
        font.setFamily("微软雅黑")
        font.setPointSize(10)
        font.setBold(False)
        font.setWeight(50)
        self.txt_type_zzgjz.setFont(font)
        self.txt_type_zzgjz.setObjectName("txt_type_zzgjz")
        self.formLayout.setWidget(2, QtWidgets.QFormLayout.FieldRole, self.txt_type_zzgjz)
        self.label_6 = QtWidgets.QLabel(self.groupBox2)
        font = QtGui.QFont()
        font.setFamily("微软雅黑")
        font.setPointSize(9)
        font.setBold(False)
        font.setWeight(50)
        self.label_6.setFont(font)
        self.label_6.setObjectName("label_6")
        self.formLayout.setWidget(3, QtWidgets.QFormLayout.LabelRole, self.label_6)
        self.txt_type_gygjz = QtWidgets.QLineEdit(self.groupBox2)
        font = QtGui.QFont()
        font.setFamily("微软雅黑")
        font.setPointSize(10)
        font.setBold(False)
        font.setWeight(50)
        self.txt_type_gygjz.setFont(font)
        self.txt_type_gygjz.setObjectName("txt_type_gygjz")
        self.formLayout.setWidget(3, QtWidgets.QFormLayout.FieldRole, self.txt_type_gygjz)
        self.verticalLayout_6.addLayout(self.formLayout)
        self.verticalLayout_7.addWidget(self.groupBox2)
        self.groupBox1 = QtWidgets.QGroupBox(self.scrollAreaWidgetContents)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.groupBox1.sizePolicy().hasHeightForWidth())
        self.groupBox1.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setFamily("微软雅黑")
        font.setPointSize(10)
        font.setBold(True)
        font.setWeight(75)
        self.groupBox1.setFont(font)
        self.groupBox1.setObjectName("groupBox1")
        self.verticalLayout_5 = QtWidgets.QVBoxLayout(self.groupBox1)
        self.verticalLayout_5.setObjectName("verticalLayout_5")
        self.verticalLayout_4 = QtWidgets.QVBoxLayout()
        self.verticalLayout_4.setObjectName("verticalLayout_4")
        self.label_2 = QtWidgets.QLabel(self.groupBox1)
        font = QtGui.QFont()
        font.setFamily("微软雅黑")
        font.setPointSize(9)
        font.setBold(False)
        font.setWeight(50)
        self.label_2.setFont(font)
        self.label_2.setObjectName("label_2")
        self.verticalLayout_4.addWidget(self.label_2)
        self.horizontalLayout_5 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_5.setObjectName("horizontalLayout_5")
        self.txt_PotentialLandFile = QtWidgets.QLineEdit(self.groupBox1)
        font = QtGui.QFont()
        font.setFamily("微软雅黑")
        font.setPointSize(9)
        font.setBold(False)
        font.setWeight(50)
        self.txt_PotentialLandFile.setFont(font)
        self.txt_PotentialLandFile.setObjectName("txt_PotentialLandFile")
        self.horizontalLayout_5.addWidget(self.txt_PotentialLandFile)
        spacerItem1 = QtWidgets.QSpacerItem(13, 20, QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_5.addItem(spacerItem1)
        self.btn_addPotentialLandFile = QtWidgets.QPushButton(self.groupBox1)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.btn_addPotentialLandFile.sizePolicy().hasHeightForWidth())
        self.btn_addPotentialLandFile.setSizePolicy(sizePolicy)
        self.btn_addPotentialLandFile.setText("")
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/icons/icons/GenericOpen32.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.btn_addPotentialLandFile.setIcon(icon)
        self.btn_addPotentialLandFile.setObjectName("btn_addPotentialLandFile")
        self.horizontalLayout_5.addWidget(self.btn_addPotentialLandFile)
        self.verticalLayout_4.addLayout(self.horizontalLayout_5)
        self.tbl_PotentialLandField = QtWidgets.QTableWidget(self.groupBox1)
        font = QtGui.QFont()
        font.setFamily("Microsoft YaHei UI")
        font.setPointSize(9)
        font.setBold(False)
        font.setWeight(50)
        self.tbl_PotentialLandField.setFont(font)
        self.tbl_PotentialLandField.setObjectName("tbl_PotentialLandField")
        self.tbl_PotentialLandField.setColumnCount(0)
        self.tbl_PotentialLandField.setRowCount(0)
        self.verticalLayout_4.addWidget(self.tbl_PotentialLandField)
        self.verticalLayout_5.addLayout(self.verticalLayout_4)
        self.verticalLayout_3 = QtWidgets.QVBoxLayout()
        self.verticalLayout_3.setSpacing(2)
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.label_3 = QtWidgets.QLabel(self.groupBox1)
        font = QtGui.QFont()
        font.setFamily("微软雅黑")
        font.setPointSize(9)
        font.setBold(False)
        font.setWeight(50)
        self.label_3.setFont(font)
        self.label_3.setObjectName("label_3")
        self.verticalLayout_3.addWidget(self.label_3)
        self.horizontalLayout_6 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_6.setObjectName("horizontalLayout_6")
        self.txt_GridFile = QtWidgets.QLineEdit(self.groupBox1)
        font = QtGui.QFont()
        font.setFamily("微软雅黑")
        font.setPointSize(9)
        font.setBold(False)
        font.setWeight(50)
        self.txt_GridFile.setFont(font)
        self.txt_GridFile.setObjectName("txt_GridFile")
        self.horizontalLayout_6.addWidget(self.txt_GridFile)
        spacerItem2 = QtWidgets.QSpacerItem(13, 20, QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_6.addItem(spacerItem2)
        self.btn_addGridFile = QtWidgets.QPushButton(self.groupBox1)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.btn_addGridFile.sizePolicy().hasHeightForWidth())
        self.btn_addGridFile.setSizePolicy(sizePolicy)
        self.btn_addGridFile.setText("")
        self.btn_addGridFile.setIcon(icon)
        self.btn_addGridFile.setIconSize(QtCore.QSize(16, 16))
        self.btn_addGridFile.setObjectName("btn_addGridFile")
        self.horizontalLayout_6.addWidget(self.btn_addGridFile)
        self.verticalLayout_3.addLayout(self.horizontalLayout_6)
        self.tbl_GridField = QtWidgets.QTableWidget(self.groupBox1)
        font = QtGui.QFont()
        font.setFamily("Microsoft YaHei UI")
        font.setPointSize(9)
        font.setBold(False)
        font.setWeight(50)
        self.tbl_GridField.setFont(font)
        self.tbl_GridField.setObjectName("tbl_GridField")
        self.tbl_GridField.setColumnCount(0)
        self.tbl_GridField.setRowCount(0)
        self.verticalLayout_3.addWidget(self.tbl_GridField)
        self.verticalLayout_5.addLayout(self.verticalLayout_3)
        self.verticalLayout_7.addWidget(self.groupBox1)
        spacerItem3 = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout_7.addItem(spacerItem3)
        self.buttonBox = QtWidgets.QDialogButtonBox(self.scrollAreaWidgetContents)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.verticalLayout_7.addWidget(self.buttonBox)
        self.verticalLayout.addLayout(self.verticalLayout_7)
        self.scrollArea.setWidget(self.scrollAreaWidgetContents)
        self.horizontalLayout_2.addWidget(self.scrollArea)

        self.retranslateUi(frmModelCal)
        QtCore.QMetaObject.connectSlotsByName(frmModelCal)

    def retranslateUi(self, frmModelCal):
        _translate = QtCore.QCoreApplication.translate
        frmModelCal.setWindowTitle(_translate("frmModelCal", "Form"))
        self.label_9.setText(_translate("frmModelCal", "优化方案名称："))
        self.groupBox3.setTitle(_translate("frmModelCal", "步骤1：优化方案的目标权重"))
        self.label_7.setText(_translate("frmModelCal", "目标1:新增总居住建筑量"))
        self.label_8.setText(_translate("frmModelCal", "目标2:拆除总建筑量"))
        self.label_10.setText(_translate("frmModelCal", "目标3:职住平衡指数"))
        self.label_11.setText(_translate("frmModelCal", "目标4:交通可达性"))
        self.label_12.setText(_translate("frmModelCal", "目标5:公共服务水平"))
        self.groupBox2.setTitle(_translate("frmModelCal", "步骤2：每类居住专规用地的使用约束"))
        self.label.setText(_translate("frmModelCal", "总城市更新计划用地的使用率"))
        self.label_4.setText(_translate("frmModelCal", "总土地整备计划用地的使用率"))
        self.label_5.setText(_translate("frmModelCal", "总旧住宅区改居住用地的使用率"))
        self.label_6.setText(_translate("frmModelCal", "总旧工业区改居住用地的使用率"))
        self.groupBox1.setTitle(_translate("frmModelCal", "步骤3：优化传导空间数据的导入"))
        self.label_2.setText(_translate("frmModelCal", "选择居住专规潜力用地图层"))
        self.label_3.setText(_translate("frmModelCal", "选择标准单元图层"))
import icons_rc
