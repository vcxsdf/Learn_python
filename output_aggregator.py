
import time
import threading
from datetime import datetime, timedelta
import pandas as pd
import sys
import paramiko # for sending output file to server using ssh

def main():
    # ...

    thread_controller(data_input, threshold_duration, db_file, table_name, delay_msg_queue_cleared, delay_signal_display, s_hostname, s_port, s_username, s_password, s_local_file, s_remote_path)

    # while True:
    #     continue
    # 最晚到1:26pm就結束
    now = datetime.now()
    while now < datetime(year = now.year, month = now.month, \
        day = now.day, hour = 13, minute =26) :
        time.sleep(30)
        now = datetime.now()

    print('~~~ Program terminate ~~~')

def check_input_duplication(data_input):
    duplicate_stock_ids = data_input[data_input['stock_id'].duplicated(keep=False)]['stock_id']
    unique_duplicates = duplicate_stock_ids.unique() # Get unique duplicate values
    if len(unique_duplicates)==0:
        print("No duplicated values in 'stock_id'")
    else:
        print("ERROR: Duplicated values in 'stock_id':", unique_duplicates)
        sys.exit(0)  # Exit with status code 0 (success)

def thread_controller(data_input, threshold_duration, db_file, table_name, delay_msg_queue_cleared, delay_signal_display, s_hostname, s_port, s_username, s_password, s_local_file, s_remote_path):
    global msg_queue
    lock = threading.Lock()         # 建立 Lock

    threads = []
    for ticker in data_input['stock_id']:
        ticker_input = data_input[data_input['stock_id'] == ticker] 
        thread = threading.Thread(target=stock_listener, args=(ticker, msg_queue[ticker], ticker_input['threshold_high'].iloc[0], ticker_input['threshold_low'].iloc[0], threshold_duration, db_file, table_name, delay_msg_queue_cleared,))
        threads.append(thread)
        # print("start thread for ", ticker, "with threshold", ticker_input['threshold_high'].iloc[0])

    for run_threads in threads:
        run_threads.daemon = True
        run_threads.start()

    t_output_aggregated_signals = threading.Thread(target=output_aggregated_signals, args=(data_input, delay_signal_display, delay_msg_queue_cleared, threshold_duration,))  #建立執行緒
    t_output_aggregated_signals.daemon = True  # daemon 參數設定為 True，則當主程序退出，執行緒也會跟著結束
    t_output_aggregated_signals.start()  #執行
    t_upload_to_http_server = threading.Thread(target=upload_to_http_server, args=(delay_signal_display, s_hostname, s_port, s_username, s_password, s_local_file, s_remote_path,))  #建立執行緒
    t_upload_to_http_server.daemon = True  # daemon 參數設定為 True，則當主程序退出，執行緒也會跟著結束
    t_upload_to_http_server.start()  #執行

def upload_to_http_server(delay_signal_display, s_hostname, s_port, s_username, s_password, s_local_file, s_remote_path):
    time.sleep(delay_signal_display)
    while True:
        ssh_push_file(s_hostname, s_port, s_username, s_password, s_local_file, s_remote_path)
        time.sleep(delay_signal_display)

def output_aggregated_signals(data_input, delay_signal_display, delay_msg_queue_cleared, threshold_duration,):
    global accumulated_duration # "ticker", "High_duration", "Low_duration"
    global first_state_change # "ticker", "High_initiation", "Low_initiation"
    global state_changes
    delay_signal_display_ms = delay_signal_display*1000 # sec to milliseconds
    # 放監測使用條件 在網頁footer 
    input_parameters = data_input[['類型', 'threshold_high', 'threshold_low']].drop_duplicates()
    type_counts = data_input['類型'].value_counts()
    input_parameters['監測數量'] = input_parameters['類型'].map(type_counts)
    parameter_table_html = '''<div style='flex: 1;'> <p></p><table style='color: white; font-size: 10px;'>
                        <tr><th>類型</th><th>高檔條件</th><th>低檔條件</th><th>監測數量</th></tr>'''
    for index, row in input_parameters.iterrows():
        parameter_table_html += "<tr><td>{}</td><td>{}</td><td>{}</td><td>{}</td></tr>".format(row['類型'], row['threshold_high'], row['threshold_low'], row['監測數量'])
    parameter_table_html += "</table></div>" 

    while True:
        print("delaying ", datetime.now())
        time.sleep(delay_signal_display)
        
        output = pd.DataFrame()
        output = data_input
        # print(output)
        # print(accumulated_duration)
        # print(first_state_change)
        if accumulated_duration.empty or first_state_change.empty:
            continue
        output = pd.merge(output, accumulated_duration, left_on='stock_id', right_index=True, how='left')
        output = pd.merge(output, first_state_change, left_on='stock_id', right_index=True, how='left')

        for ticker in output['stock_id']:
            if state_changes[ticker] != []:
                if state_changes[ticker][-1]['state'] == 'high':
                    output.loc[output['stock_id'] == ticker, 'current_state'] = '高'
                elif state_changes[ticker][-1]['state'] == 'low':
                    output.loc[output['stock_id'] == ticker, 'current_state'] = '低'

        output = output.reindex(columns=['stock_id', '公司簡稱', '類型', 'High_initiation', 'High_duration', 'Low_initiation', 'Low_duration', 'current_state', '是否為股票期貨標的','pct_delta'])
        output.dropna(subset=['High_initiation', 'Low_initiation'], how='all', inplace=True)
        output = output.sort_values(by='current_state', ascending=True) #
        output = output.rename(columns={'stock_id': '代碼', '公司簡稱': '簡稱', '是否為股票期貨標的': '股期', 'High_initiation': '高檔開始', 'High_duration': '高檔時長', 'Low_initiation': '低檔開始', 'Low_duration': '低檔時長', 'current_state': '當前信號', 'pct_delta': '大戶增減%'})

        print(datetime.now().strftime("%H:%M:%S")) # 只輸出 hour, minute, second
        # print(output.to_markdown(index=False, numalign="left", stralign="left")) # 全資料一張表

        # Create HTML content with tabs for each table
        html_content = f'''
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>監測信號輸出</title>
            <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/4.0.0/css/bootstrap.min.css">
            <style>
              td, th {{
                  text-align: center; 
                  vertical-align: middle; 
              }}
              footer {{
                background-color: #333;
                color: white; 
                padding: 6px; /* Add padding to create some space */
                text-align: left; 
                font-size: 10px; 
              }}
            </style>
        </head>
        <body>
        <main>
            <ul class="nav nav-tabs" id="myTab" role="tablist">
        '''
        grouped_output = output.groupby('類型')
        group_names = output['類型'].unique()
        # print(len(group_names))
        # print(group_names)
        for i, name in enumerate(group_names, start=1): # for creating a list on top of the html page
            active_class = "show active" if i == 1 else ""
            html_content += f'''<li class="nav-item">
                                <a class="nav-link {active_class}" id="output{i}-tab" data-toggle="tab" href="#output{i}" role="tab" aria-controls="output{i}" aria-selected="true"><b>{name}</b></a>
                            </li>
                            '''
        html_content += f'''
            </ul>
            <div class="tab-content" id="myTabContent">
        '''
        for i, name in enumerate(group_names, start=1):
            html_content += html_table_handler(grouped_output, i, name) # also print table 
        html_content += f'''</div>
                </main>
                <footer>
                <div style='display: flex;'> <div style='flex: 1;'>
                <p></p>
                    </div>
                '''
        html_content += parameter_table_html
        html_content += f'''
                </ul></div>
            </footer>
                <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
                <script src="https://cdnjs.cloudflare.com/ajax/libs/popper.js/1.16.0/umd/popper.min.js"></script>
                <script src="https://maxcdn.bootstrapcdn.com/bootstrap/4.0.0/js/bootstrap.min.js"></script>
                <script>
                    var sortingOrder1 = []; // Keeps track of sorting order for table 1
                    var sortingOrder2 = []; // Keeps track of sorting order for table 2
                    var sortingOrder3 = []; // Keeps track of sorting order for table 3

                    function sortTable(tableId, colIndex, sortingOrder) {{
                        var table = document.getElementById(tableId);
                        var tbody = table.getElementsByTagName("tbody")[0];
                        var rows = Array.from(tbody.getElementsByTagName("tr"));

                        sortingOrder[colIndex] = !sortingOrder[colIndex]; // Toggle sorting order

                        rows.sort((a, b) => {{
                            var aValue = a.getElementsByTagName("td")[colIndex].innerText;
                            var bValue = b.getElementsByTagName("td")[colIndex].innerText;

                            if (sortingOrder[colIndex]) {{
                                return aValue.localeCompare(bValue);
                            }} else {{
                                return bValue.localeCompare(aValue);
                            }}
                        }});

                        rows.forEach(row => tbody.appendChild(row));
                    }}

                    document.addEventListener("DOMContentLoaded", function () {{
                        var headers1 = document.querySelectorAll("#myTable1 th");
                        var headers2 = document.querySelectorAll("#myTable2 th");
                        var headers3 = document.querySelectorAll("#myTable3 th");

                        headers1.forEach((header, index) => {{
                            sortingOrder1[index] = false; // Initialize sorting order for each column
                            header.addEventListener("click", function () {{
                                sortTable("myTable1", index, sortingOrder1);
                            }});
                        }});

                        headers2.forEach((header, index) => {{
                            sortingOrder2[index] = false; // Initialize sorting order for each column
                            header.addEventListener("click", function () {{
                                sortTable("myTable2", index, sortingOrder2);
                            }});
                        }});

                        headers3.forEach((header, index) => {{
                            sortingOrder3[index] = false; // Initialize sorting order for each column
                            header.addEventListener("click", function () {{
                                sortTable("myTable3", index, sortingOrder3);
                            }});
                        }});
                    }});
                    // Auto-refresh every {delay_signal_display} seconds
                    setInterval(function() {{
                        window.location.reload(true);
                    }}, {delay_signal_display_ms});
                </script>
            </body>
            </html>
        '''
        # 輸出檔案 到\Python_codes (python compiler目錄)
        with open('output_tabs.html', 'w', encoding='utf-8') as f:
            f.write(html_content)

def html_table_handler(grouped_output, group_order, group_name):
    sortedby = '當前信號' #default
    if group_name == '收黑':
        sortedby = '高檔時長'
    elif group_name == '收紅':
        sortedby = '低檔時長'
    elif group_name == '自選':
        sortedby = '高檔時長'
    table_grouped = grouped_output.get_group(group_name).drop(columns=['類型'])
    table_sorted = table_grouped.sort_values(by=sortedby, ascending=False)
    print(">>>",group_name,"<<<")
    print(table_sorted.to_markdown(index=True, numalign="left", stralign="left"))
    table_to_html = table_sorted
    table_to_html['大戶增減%'] = table_to_html.apply(generate_hyperlink, args=('大戶增減%',), axis=1)
    table_to_html['簡稱'] = table_to_html.apply(generate_hyperlink, args=('簡稱',), axis=1)
    output_html = table_to_html.to_html(classes='table table-striped', header=True, index=False, na_rep='', escape=False)
    table_str = '<table id="myTable{}" class="table sortable table-striped"'.format(group_order)
    output_html_with_bootstrap = output_html.replace('<table', table_str)
    active_class = "show active" if group_order == 1 else ""
    html_content = f'''<div class="tab-pane fade {active_class}" id="output{group_order}" role="tabpanel" aria-labelledby="output{group_order}-tab">
                        {output_html_with_bootstrap}
                    </div>'''
    return html_content

def generate_hyperlink(row, type):
    stock_id = row['代碼']
    if type == '大戶增減%':
        value = row['大戶增減%']
        if value < 0:
            color = 'green'
        else:
            color = 'red'
        output = f'<a href="https://www.wantgoo.com/stock/{stock_id}/major-investors/concentration" target="_blank" style="color: {color};">{value}</a>'
    elif type == '簡稱':
        value = row['簡稱']
        output = f'<a href="https://histock.tw/stock/{stock_id}" target="_blank">{value}</a>'
    return output

def ssh_push_file(hostname, port, username, password, local_file, remote_path):
# def ssh_push_file(hostname, port, username, private_key_file, local_file, remote_path):
    # Initialize SSH client
    ssh = paramiko.SSHClient()
    ssh.load_system_host_keys()  # Load known_hosts file
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    # Load private key
    # private_key = paramiko.RSAKey.from_private_key_file(private_key_file)

    try:
        # Connect to the server
        ssh.connect(hostname, port=port, username=username, password=password, look_for_keys=False, allow_agent=False)
        # ssh.connect(hostname, port=port, username=username, pkey=private_key)

        # Use SFTP to push file
        sftp = ssh.open_sftp()
        sftp.put(local_file, remote_path)
        sftp.close()

        print(f"File '{local_file}' pushed to '{remote_path}' successfully.")

    except paramiko.AuthenticationException as auth_err:
        print(f"Authentication failed: {auth_err}")
    except paramiko.SSHException as ssh_err:
        print(f"SSH connection failed: {ssh_err}")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        # Disconnect SSH session
        ssh.close()