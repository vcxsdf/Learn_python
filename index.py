from ctypes import *
import os
import xml.etree.ElementTree as ET
import tkinter as tk
from tkinter import *


#傳參數到dll前要先轉換
def ConvertToDllStr(tmp):
   return tmp.encode('mbcs')

#dll事件回傳轉字串
def ConvertStrFromDll(tmp):
   if tmp == None:
      return ""
   else:
      return tmp.decode('mbcs')

#預設帳號, 密碼
default_Account = "F123456789"
default_Pwd = "a123456"
default_StockNo = "2303"
default_Price = "16"

default_IP = "itstradeuat.pscnet.com.tw"
default_Port = "11002"

dict ={}

#初始化dll
dllpath = os.path.dirname(os.path.abspath(__file__)) + os.path.sep + "RayinVTS_64.dll"
print(dllpath)
dll = windll.LoadLibrary(dllpath)

#設定初始下單資料
def SetDefaultOrderData():
    edt_stockno.insert(0, default_StockNo)
    edt_apcode.insert(0, "1")
    edt_bs.insert(0, "B")
    edt_price.insert(0, default_Price)
    edt_pflag.insert(0, "0")
    edt_qty.insert(0, "2")
    edt_bsflag.insert(0, "R")

    edt_ordType.insert(0, "0")

    edt_chg_stockno.insert(0, default_StockNo)
    edt_chgprice.insert(0, default_Price)
    edt_chgqty.insert(0, "1")

#初始化接收事件
def onLoginEvent(status):
    s = ConvertStrFromDll(status)
    print(s)

    login_mes.delete(0, END)
    login_mes.insert(0, s)

    root = ET.fromstring(s)
    ret = root.find("ret")

    #print(ret.get("status"), ret.get("msg"))
    if ret.get("status") == "OK":
        print("Receive Login OK")
        dll.ConnectToOrderServer()
        dll.ConnectToAckMatServer()
        dll.ConnectToQuoteServer()
        acc = root.find("list").find("acc")

        cust_id = acc.attrib["cust_id"]
        edt_branch.insert(0, acc.attrib["bhno4"])
        edt_custid.insert(0, cust_id)

        edt_chg_branch.insert(0, acc.attrib["bhno4"])
        edt_chg_custid.insert(0, cust_id)

        SetDefaultOrderData()
    else:
        print("Receive login Error")
        print(ConvertStrFromDll(status))

def onOrderConnect():
    print("下單已連線")

#接收主動回報
AryAck = []
def onNewAck(LineNo, ClOrdId, OrgClOrdId, BranchId, Account, OrderDate, OrderTime, OrderID, Symbol, ExCode, Side,
             OrdType, PriceFlag, Price, OrderQty, errCode, errMsg, ExecType, BeforeQty, AfterQty, TimeInForce,
             UserData):
    print("onNewAck")
    msg = 'ClOrdId=' + ConvertStrFromDll(ClOrdId)
    msg += 'UserData=' + ConvertStrFromDll(UserData)
    msg += '帳號=' + ConvertStrFromDll(Account)
    msg +=',ExecType=' + ConvertStrFromDll(ExecType)
    msg +=',errCode=' + ConvertStrFromDll(errCode)
    msg += ',委託書號=' + ConvertStrFromDll(OrderID)
    msg +=',股票代碼=' + ConvertStrFromDll(Symbol)
    msg +=',委託價格=' + str(round(float(Price), 2))
    msg +=',B/S=' + str(Side)
    msg +=',數量=' + str(BeforeQty)
    msg +=',改量=' + str(AfterQty)
    msg += ',回報日期=' + ConvertStrFromDll(OrderDate)
    msg +=',回報時間=' + ConvertStrFromDll(OrderTime[:6])
    #print(msg)
    list_Ack.insert(0, msg)


    #將新單的委託書號帶入改單欄位
    if ExecType == b'O':
        edt_chg_orderno.delete(0, END)
        edt_chg_orderno.insert(0, ConvertStrFromDll(OrderID))



def onAckMatConnect():
    print("回報已連線")
    #回補電文
    dll.Recover(ConvertToDllStr("0"))

def onQuoteEvent(quote):
    lst_quote.insert(0, ConvertStrFromDll(quote))


def onQuoteConnect():
    print("行情已連線")
    """
    for widget in Show_Quote_Frame.winfo_children():
        widget.destroy()

    
    """

def onOrderDisConnect():
    print("onOrderDisConnect")

def onAckMatDisConnect():
    print("onAckMatDisConnect")

def onQuoteDisConnect():
    print("onQuoteDisConnect")

def OnOdrServerError(errCode, errMsg):
    print("OnOdrServerError")
    c = str(errCode)
    m = ConvertStrFromDll(errMsg)
    print(c + "," + m)

def OnAckMatServerError(errCode, errMsg):
    print("OnAckMatServerError")
    c = str(errCode)
    m = ConvertStrFromDll(errMsg)
    print(c + "," + m)

def onNewMat(lineno, branch_id, cust_id, ordno, Symbol, ExCode, buysell, trade, mat_time, mat_price, mat_qty, mkt_seq_num):
    #print("onNewMat")

    msg = 'lineno=' + ConvertStrFromDll(lineno)
    msg += ',branch_id=' + ConvertStrFromDll(branch_id)
    msg += ',cust_id=' + ConvertStrFromDll(cust_id)
    msg += ',ordno=' + ConvertStrFromDll(ordno)
    msg += ',Symbol=' + ConvertStrFromDll(Symbol)
    msg += ',ExCode=' + str(ExCode)
    msg += ',buysell=' + ConvertStrFromDll(buysell)
    msg += ',trade=' + ConvertStrFromDll(trade)
    msg += ',mat_time=' + ConvertStrFromDll(mat_time)
    msg += ',mat_price=' + str(mat_price)
    msg += ',mat_qty=' + str(mat_qty)
    msg += ',mkt_seq_num=' + ConvertStrFromDll(mkt_seq_num)

    list_Mat.insert(0, msg)

def onMsgAlertEvent(errCode, errMsg):
    print("onMsgAlertEvent")
    c = str(errCode)
    m = ConvertStrFromDll(errMsg)
    print(c + "," + m)

def OnInstantAck(ExecType, ClOrdId, BranchId, Account, OrderDate, OrderTime, OrderID, Symbol, ExCode, Side, OrdType, PriceFlag, Price, OrderQty, BeforeQty, AfterQty, TimeInForce, errCode, errMsg):
    print("OnInstantAck")

    msg = '帳號=' + ConvertStrFromDll(Account)
    msg += ',ExecType=' + ConvertStrFromDll(ExecType)
    msg += ',errCode=' + ConvertStrFromDll(errCode)
    msg += ',errMsg=' + ConvertStrFromDll(errMsg)
    msg += ',委託書號=' + ConvertStrFromDll(OrderID)
    msg += ',股票代碼=' + ConvertStrFromDll(Symbol)
    msg += ',委託價格=' + str(round(float(Price), 2))
    msg += ',B/S=' + str(Side)
    msg += ',數量=' + str(BeforeQty)
    msg += ',改量=' + str(AfterQty)
    msg += ',回報日期=' + ConvertStrFromDll(OrderDate)
    msg += ',回報時間=' + ConvertStrFromDll(OrderTime[:6])
    print(msg)
#設定callbck
onConnectType = WINFUNCTYPE(None)
orderconnect = onConnectType(onOrderConnect)    #下單連線
orderdisconnect = onConnectType(onOrderDisConnect)    #下單斷線

ackmatconnect = onConnectType(onAckMatConnect)  #回報連線
ackmatdisconnect = onConnectType(onAckMatDisConnect)  #回報斷線

quoteconnect = onConnectType(onQuoteConnect)    #行情連線
quotedisconnect = onConnectType(onQuoteDisConnect)    #行情斷線

callback_type = WINFUNCTYPE(None, c_char_p)
callback_login = callback_type(onLoginEvent) #登入
callback_quote = callback_type(onQuoteEvent) #行情報價

callback_type_error = WINFUNCTYPE(None, c_int, c_char_p)
onOdrErr = callback_type_error(OnOdrServerError) #下單錯誤
onAckMatErr = callback_type_error(OnAckMatServerError) #主回錯誤
onMsgAlert = callback_type_error(onMsgAlertEvent) #訊息提醒

onNewAckType = WINFUNCTYPE(None, c_char_p, c_char_p, c_char_p, c_char_p, c_char_p, c_char_p, c_char_p, c_char_p, c_char_p, c_int, c_char_p, c_char_p, c_int, c_float, c_int, c_char_p, c_char_p, c_char_p, c_int, c_int, c_char_p, c_char_p)
onnewack = onNewAckType(onNewAck)   #主動回報

onNewMatType = WINFUNCTYPE(None, c_char_p, c_char_p, c_char_p, c_char_p, c_char_p, c_int, c_char_p, c_char_p, c_char_p, c_float, c_int, c_char_p)
onnewmat = onNewMatType(onNewMat)   #成交回報

onInstAckType = WINFUNCTYPE(None, c_char_p, c_char_p, c_char_p, c_char_p, c_char_p, c_char_p, c_char_p, c_char_p, c_int, c_char_p, c_char_p, c_int, c_float, c_int, c_int, c_int, c_char_p, c_char_p, c_char_p)
oninstack = onInstAckType(OnInstantAck)   #主動回報

#初始化設定
dll.SetFastQuote(True)
dll.SetDebugMode(True)
dll.SetSerialNo("")
dll.SetRecvTimeout(0)
dll.SetOnLoginEvent.argtypes = [callback_type]
dll.SetOnLoginEvent(callback_login) #設定登入回傳事件

dll.SetOnOdrConnectEvent(orderconnect) #設定下單連線r事件
dll.SetOnOdrDisConnectEvent(orderdisconnect) #設定下單斷線事件
dll.SetOnOdrErrorEvent(onOdrErr) #設定下單連線異常事件

dll.SetOnAckMatConnectEvent(ackmatconnect) #設定回報連線事件
dll.SetOnAckMatDisConnectEvent(ackmatdisconnect) #設定回報斷線事件
dll.SetOnAckMatErrorEvent(onAckMatErr) #設定回報連線異常事件

dll.SetOnQuoteConnectEvent(quoteconnect) #設定行情連線事件
dll.SetOnQuoteDisConnectEvent(quotedisconnect) #設定行情斷線事件

dll.SetNewAckEvent.argtypes = [onNewAckType]
dll.SetNewAckEvent(onnewack) #設定主動委託回報事件

dll.SetNewMatEvent.argtypes = [onNewMatType]
dll.SetNewMatEvent(onnewmat) #設定主動成交回報事件

dll.SetNewQuoteEvent.argtypes = [callback_type]
dll.SetNewQuoteEvent(callback_quote) #設定新行情事件

dll.SetMsgAlertEvent(onMsgAlert) #設定訊息提醒事件

dll.SetOnInstantAckEvent(oninstack) #主動回報(此dll)


#設定button行為事件
def btn_LoginClick():
    print('btn_LoginClick')
    # ---------------設定dns、port---------------------
    dll.SetServer(ConvertToDllStr(edt_IP.get()), int(edt_port.get()))
    # ------------------------------------

    rv = dll.Login(ConvertToDllStr(edt_user.get()), ConvertToDllStr(edt_pass.get()))
    if(bool(rv)):
        print("login OK")
        #login_mes.insert(0, "login OK")
        login_mes.delete(0, END)
        login_mes.insert(0, "login OK")
        #tmb.showinfo("登入", "登入成功")
    else:
        print("login error")
        login_mes.delete(0, END)
        login_mes.insert(0, "login error")
        #tmb.showinfo("登入", "登入錯誤")

    #print(rv)

def btn_neworderClick():
    print('btn_neworderClick')
    requestno = c_char_p(b"")
    errcode = c_char_p(b"")
    errMsg = c_char_p(b"")
    branch_id = ConvertToDllStr(edt_branch.get())
    custid = ConvertToDllStr(edt_custid.get())
    stockno = ConvertToDllStr(edt_stockno.get())
    bs = ConvertToDllStr(edt_bs.get())
    bsflag = ConvertToDllStr(edt_bsflag.get())
    price = c_float(float(edt_price.get()))

    ordType = ConvertToDllStr(edt_ordType.get())

    dll.NewOrder(branch_id, custid, stockno, int(edt_apcode.get()), bs, ordType, price,
                 int(edt_pflag.get()), int(edt_qty.get()), bsflag, ConvertToDllStr("Python dll Test"),
                 pointer(requestno), pointer(errcode), pointer(errMsg))

    edt_msg.delete(0, END)
    edt_msg.insert(0, 'requestno=' + ConvertStrFromDll(requestno.value) + ',errcode=' + ConvertStrFromDll(
        errcode.value) + ',errmsg=' + ConvertStrFromDll(errMsg.value))

#訂閱股號
def btn_AddQuoteClick():
    print("btn_AddQuoteClick")
    errCode = c_char_p(b"")
    errMsg = c_char_p(b"")
    print(ConvertToDllStr(edt_quote.get()))
    rv = dll.AddQuote(0, ConvertToDllStr(edt_quote.get()), pointer(errCode), pointer(errMsg))
    #print(ConvertStrFromDll(errCode))
    #print(ConvertStrFromDll(errMsg))
    print(errMsg)

def btn_ChgPriceOrderClick():
    print("btn_ChgPriceOrderClick")
    edt_chg_msg.delete(0, END)
    ClOrdId = c_char_p(b"")
    errCode = c_char_p(b"")
    errMsg = c_char_p(b"")
    branch_id = ConvertToDllStr(edt_chg_branch.get())
    custid = ConvertToDllStr(edt_chg_custid.get())
    orderid = ConvertToDllStr(edt_chg_orderno.get())
    stockno = ConvertToDllStr(edt_chg_stockno.get())
    #bs = ConvertToDllStr(edt_bs.get())
    price = c_float(round(float(edt_chgprice.get()), 2))
    
    
    print(price)
    dll.ChgPriceOrder(branch_id, custid, orderid, stockno, "0", 1, price,
                 0, "R", ConvertToDllStr("Python dll Test"),
                 pointer(ClOrdId), pointer(errCode), pointer(errMsg))


    edt_chg_msg.insert(0, 'ClOrdId=' + ConvertStrFromDll(ClOrdId.value) + ',errcode=' + ConvertStrFromDll(
        errCode.value) + ',errmsg=' + ConvertStrFromDll(errMsg.value))

def btn_ChgQtyOrderClick():
    ClOrdId = c_char_p(b"")
    errCode = c_char_p(b"")
    errMsg = c_char_p(b"")
    branch_id = ConvertToDllStr(edt_chg_branch.get())
    custid = ConvertToDllStr(edt_chg_custid.get())
    orderid = ConvertToDllStr(edt_chg_orderno.get())
    stockno = ConvertToDllStr(edt_chg_stockno.get())
    #bs = ConvertToDllStr(edt_bs.get())
    #price = c_float(float(edt_chgprice.get()))
    qty = int(edt_chgqty.get())
    print("qty" + str(qty))
    dll.ChgQtyOrder(branch_id, custid, orderid, stockno, "0", 1, qty,
                 0, ConvertToDllStr("Python dll Test"),
                 pointer(ClOrdId), pointer(errCode), pointer(errMsg))

    edt_chg_msg.delete(0, END)
    edt_chg_msg.insert(0, 'ClOrdId=' + ConvertStrFromDll(ClOrdId.value) + ',errcode=' + ConvertStrFromDll(
        errCode.value) + ',errmsg=' + ConvertStrFromDll(errMsg.value))


def btn_ChgCancelOrderClick():
    ClOrdId = c_char_p(b"")
    errCode = c_char_p(b"")
    errMsg = c_char_p(b"")
    branch_id = ConvertToDllStr(edt_chg_branch.get())
    custid = ConvertToDllStr(edt_chg_custid.get())
    orderid = ConvertToDllStr(edt_chg_orderno.get())
    stockno = ConvertToDllStr(edt_chg_stockno.get())
    #bs = ConvertToDllStr(edt_bs.get())

    dll.ChgQtyOrder(branch_id, custid, orderid, stockno, "0", 1, 0,
                 0, ConvertToDllStr("Python dll Test"),
                 pointer(ClOrdId), pointer(errCode), pointer(errMsg))

    edt_chg_msg.delete(0, END)
    edt_chg_msg.insert(0, 'ClOrdId=' + ConvertStrFromDll(ClOrdId.value) + ',errcode=' + ConvertStrFromDll(
        errCode.value) + ',errmsg=' + ConvertStrFromDll(errMsg.value))


def btn_RemoveQuoteClick():
    print("btn_RemoveQuoteClick")
    errCode = c_char_p(b"")
    errMsg = c_char_p(b"")
    print(ConvertToDllStr(edt_quote.get()))
    rv = dll.DelQuote(0, ConvertToDllStr(edt_quote.get()), pointer(errCode), pointer(errMsg))
    # print(ConvertStrFromDll(errCode))
    # print(ConvertStrFromDll(errMsg))
    print(errMsg)

#建立視窗
window = tk.Tk()
window.title('統一證券(雷影)Python範例程式')
window.geometry('1350x600')

lbl_login = tk.Label(window, text='登入')
lbl_login.place(x=10, y=0)

#主機位置框
IP_frame = tk.Frame(window)
IP_frame.place(x=10,y=30)
lbl_IP = tk.Label(IP_frame, text='主機:')
lbl_IP.pack(side=tk.LEFT)
edt_IP = tk.Entry(IP_frame)
edt_IP.insert(0, default_IP)
edt_IP.pack(side=tk.LEFT)

#port框
port_frame = tk.Frame(window)
port_frame.place(x=10,y=60)
lbl_port = tk.Label(port_frame, text='Port:')
lbl_port.pack(side=tk.LEFT)
edt_port = tk.Entry(port_frame, text='')
edt_port.insert(0, default_Port)
edt_port.pack(side=tk.LEFT)


#帳號框
user_frame = tk.Frame(window)
user_frame.place(x=200,y=30)
lbl_user = tk.Label(user_frame, text='帳號:')
lbl_user.pack(side=tk.LEFT)
edt_user = tk.Entry(user_frame)
edt_user.insert(0, default_Account)
edt_user.pack(side=tk.LEFT)

#密碼框
pass_frame = tk.Frame(window)
pass_frame.place(x=200,y=60)
lbl_pass = tk.Label(pass_frame, text='密碼:')
lbl_pass.pack(side=tk.LEFT)
edt_pass = tk.Entry(pass_frame, text='ZZ123456')
edt_pass.insert(0, default_Pwd)
edt_pass.pack(side=tk.LEFT)

lbl_status = tk.Label(window, text='', width=5, height=1)
lbl_status.place(x=10, y=90)
login_mes = tk.Entry(window, text='', width=170)
login_mes.place(x=20, y=90)
btn_login = tk.Button(window, text='登入', width=5, height=1, command=btn_LoginClick)
btn_login.place(x=400, y=40)



#下單資訊框
frame = tk.Frame(window, width=500, height=300, relief="ridge", borderwidth=3, bd=3)
frame.place(x=0,y=120)

branch_frame = tk.Frame(frame)
branch_frame.pack()
lbl_branch = tk.Label(branch_frame, text='分公司代號:', anchor='e', width=10)
lbl_branch.pack(side=tk.LEFT)
edt_branch = tk.Entry(branch_frame)
edt_branch.pack(side=tk.LEFT)

custid_frame = tk.Frame(frame)
custid_frame.pack()
lbl_custid = tk.Label(custid_frame, text='客戶帳號:', anchor='e', width=10)
lbl_custid.pack(side=tk.LEFT)
edt_custid = tk.Entry(custid_frame)
edt_custid.pack(side=tk.LEFT)

stockno_frame = tk.Frame(frame)
stockno_frame.pack()
lbl_stockno = tk.Label(stockno_frame, text='股票代號:', anchor='e', width=10)
lbl_stockno.pack(side=tk.LEFT)
edt_stockno = tk.Entry(stockno_frame)
edt_stockno.pack(side=tk.LEFT)

apcode_frame = tk.Frame(frame)
apcode_frame.pack()
lbl_apcode = tk.Label(apcode_frame, text='盤別:', anchor='e', width=10)
lbl_apcode.pack(side=tk.LEFT)
edt_apcode = tk.Entry(apcode_frame, text='1')
edt_apcode.pack(side=tk.LEFT)

ordType_frame = tk.Frame(frame)
ordType_frame.pack()
lbl_ordType = tk.Label(ordType_frame, text='委託類別:', anchor='e', width=10)
lbl_ordType.pack(side=tk.LEFT)
edt_ordType = tk.Entry(ordType_frame, text='0')
edt_ordType.pack(side=tk.LEFT)

bs_frame = tk.Frame(frame)
bs_frame.pack()
lbl_bs = tk.Label(bs_frame, text='買賣別:', anchor='e', width=10)
lbl_bs.pack(side=tk.LEFT)
edt_bs = tk.Entry(bs_frame)
edt_bs.pack(side=tk.LEFT)

price_frame = tk.Frame(frame)
price_frame.pack()
lbl_price = tk.Label(price_frame, text='價格:', anchor='e', width=10)
lbl_price.pack(side=tk.LEFT)
edt_price = tk.Entry(price_frame)
edt_price.pack(side=tk.LEFT)

pflag_frame = tk.Frame(frame)
pflag_frame.pack()
lbl_pflag = tk.Label(pflag_frame, text='價格旗標:', anchor='e', width=10)
lbl_pflag.pack(side=tk.LEFT)
edt_pflag = tk.Entry(pflag_frame)
edt_pflag.pack(side=tk.LEFT)

qty_frame = tk.Frame(frame)
qty_frame.pack()
lbl_qty = tk.Label(qty_frame, text='數量:', anchor='e', width=10)
lbl_qty.pack(side=tk.LEFT)
edt_qty = tk.Entry(qty_frame)
edt_qty.pack(side=tk.LEFT)

bsflag_frame = tk.Frame(frame)
bsflag_frame.pack()
lbl_bsflag = tk.Label(bsflag_frame, text='委託條件:', anchor='e', width=10)
lbl_bsflag.pack(side=tk.LEFT)
edt_bsflag = tk.Entry(bsflag_frame)
edt_bsflag.pack(side=tk.LEFT)


neworder_frame = tk.Frame(frame)
neworder_frame.pack()
btn_neworder = tk.Button(neworder_frame, text='下單',command = btn_neworderClick)
btn_neworder.pack(side=tk.LEFT, pady=10)

msg_frame = tk.Frame(frame)
msg_frame.pack()
lbl_neworder_msg = tk.Label(msg_frame, text='訊息:')
lbl_neworder_msg.pack(side=tk.LEFT)
edt_msg = tk.Entry(msg_frame)
edt_msg.pack(side=tk.LEFT)


#---------------------------------------------
#訂閱報價資訊框
Quote_Frame = tk.Frame(window, width=500, height=300, relief="ridge", borderwidth=3, bd=3)
Quote_Frame.place(x=0,y=400)

Quote_Stock_Frame = tk.Frame(Quote_Frame)
Quote_Stock_Frame.pack()
lbl_quote = tk.Label(Quote_Stock_Frame, text='股號:', anchor='e', width=8)
lbl_quote.pack(side=tk.LEFT)
edt_quote = tk.Entry(Quote_Stock_Frame, width=8)
edt_quote.insert(0, "2303")
edt_quote.pack(side=tk.LEFT)
btn_quote = tk.Button(Quote_Stock_Frame, text='訂閱', command=btn_AddQuoteClick)
btn_quote.pack(side=tk.LEFT)

btn_remove_quote = tk.Button(Quote_Stock_Frame, text='解除訂閱', command=btn_RemoveQuoteClick)
btn_remove_quote.pack(side=tk.LEFT)


lst_quote = tk.Listbox(window, width=170, height=8, selectmode='extended')
lst_quote.place(x=5, y=450)


#改價、改量、刪單 框
frame_chg = tk.Frame(window, width=500, height=300, relief="ridge", borderwidth=3, bd=3)
frame_chg.place(x=250,y=120)

chg_branch_frame = tk.Frame(frame_chg)
chg_branch_frame.pack()
lbl_chg_branch = tk.Label(chg_branch_frame, text='分公司代號:', anchor='e', width=10)
lbl_chg_branch.pack(side=tk.LEFT)
edt_chg_branch = tk.Entry(chg_branch_frame)
edt_chg_branch.pack(side=tk.LEFT)

chg_custid_frame = tk.Frame(frame_chg)
chg_custid_frame.pack()
lbl_chg_custid = tk.Label(chg_custid_frame, text='客戶帳號:', anchor='e', width=10)
lbl_chg_custid.pack(side=tk.LEFT)
edt_chg_custid = tk.Entry(chg_custid_frame)
edt_chg_custid.pack(side=tk.LEFT)

chg_stockno_frame = tk.Frame(frame_chg)
chg_stockno_frame.pack()
lbl_chg_stockno = tk.Label(chg_stockno_frame, text='股票代號:', anchor='e', width=10)
lbl_chg_stockno.pack(side=tk.LEFT)
edt_chg_stockno = tk.Entry(chg_stockno_frame)
edt_chg_stockno.pack(side=tk.LEFT)

chg_orderno_frame = tk.Frame(frame_chg)
chg_orderno_frame.pack()
lbl_chg_orderno = tk.Label(chg_orderno_frame, text='委託書號:', anchor='e', width=10)
lbl_chg_orderno.pack(side=tk.LEFT)
edt_chg_orderno = tk.Entry(chg_orderno_frame)
edt_chg_orderno.pack(side=tk.LEFT)

chgprice_frame = tk.Frame(frame_chg)
chgprice_frame.pack()
lbl_chg_price = tk.Label(chgprice_frame, text='價格:', anchor='e', width=10)
lbl_chg_price.pack(side=tk.LEFT)
edt_chgprice = tk.Entry(chgprice_frame)
edt_chgprice.pack(side=tk.LEFT)

chgqty_frame = tk.Frame(frame_chg)
chgqty_frame.pack()
lbl_chg_qty = tk.Label(chgqty_frame, text='減量:', anchor='e', width=10)
lbl_chg_qty.pack(side=tk.LEFT)
edt_chgqty = tk.Entry(chgqty_frame)
edt_chgqty.pack(side=tk.LEFT)


chgorder_frame = tk.Frame(frame_chg)
chgorder_frame.pack()
btn_chgorder = tk.Button(chgorder_frame, text='改價',command = btn_ChgPriceOrderClick)
btn_chgorder.pack(side=tk.LEFT, pady=10)

btn_chgorderqty = tk.Button(chgorder_frame, text='減量',command = btn_ChgQtyOrderClick)
btn_chgorderqty.pack(side=tk.LEFT, padx=20)

btn_cancelorder = tk.Button(chgorder_frame, text='刪單',command = btn_ChgCancelOrderClick)
btn_cancelorder.pack(side=tk.LEFT)

chg_msg_frame = tk.Frame(frame_chg)
chg_msg_frame.pack()
lbl_chg_msg = tk.Label(chg_msg_frame, text='訊息:')
lbl_chg_msg.pack(side=tk.LEFT, pady=10)
edt_chg_msg = tk.Entry(chg_msg_frame)
edt_chg_msg.pack(side=tk.LEFT)


#主動回報顯示框
lbl_Ack_msg = tk.Label(window, text='委託回報:')
lbl_Ack_msg.place(x=500, y=120)
#list_Ack = tk.Listbox(window, listvariable=StringVar(value=AryAck))
list_Ack = tk.Listbox(window, width=120, height=10)
list_Ack.place(x=500, y=140)

#成交回報顯示框
lbl_Mat_msg = tk.Label(window, text='成交回報:')
lbl_Mat_msg.place(x=500, y=310)
list_Mat = tk.Listbox(window, width=120, height=5)
list_Mat.place(x=500, y=330)


window.mainloop()













