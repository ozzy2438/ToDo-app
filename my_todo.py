import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import networkx as nx
import matplotlib.pyplot as plt
import random
import base64
import io
import time
import plotly.express as px
from streamlit_tags import st_tags
from wordcloud import WordCloud
import calendar as cal  # calendar modülünü cal olarak import edin
from streamlit_calendar import calendar  # streamlit_calendar'dan calendar fonksiyonunu import edin

import sqlite3
import plotly.graph_objects as go
import markdown
import bcrypt
from streamlit_plotly_events import plotly_events
import streamlit_quill as sq
import pandas as pd

# Veritabanı bağlantısı ve tablo oluşturma
conn = sqlite3.connect('todo_app.db')
c = conn.cursor()

# Tabloları oluştur
c.execute('''CREATE TABLE IF NOT EXISTS users
             (id INTEGER PRIMARY KEY, username TEXT UNIQUE, password TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS tasks
             (id INTEGER PRIMARY KEY, user_id INTEGER, task TEXT, done BOOLEAN, 
             created_at TIMESTAMP, priority TEXT, tags TEXT, due_date DATE, order_index INTEGER)''')
c.execute('''CREATE TABLE IF NOT EXISTS notes
             (id INTEGER PRIMARY KEY, user_id INTEGER, title TEXT, content TEXT, 
             created_at TIMESTAMP, tags TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS links
             (id INTEGER PRIMARY KEY, user_id INTEGER, source TEXT, target TEXT, type TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS goals
             (id INTEGER PRIMARY KEY, user_id INTEGER, goal TEXT, target_date DATE, completed BOOLEAN)''')
c.execute('''CREATE TABLE IF NOT EXISTS subtasks
             (id INTEGER PRIMARY KEY, task_id INTEGER, subtask TEXT, done BOOLEAN)''')
c.execute('''CREATE TABLE IF NOT EXISTS note_attachments
             (id INTEGER PRIMARY KEY, note_id INTEGER, file_name TEXT, file_content BLOB)''')
conn.commit()

# Takvim verilerini hazırla
calendar_data = []
from streamlit import session_state

# Veritabanından görevleri al
tasks = []
if 'user_id' in session_state:
    for row in c.execute("SELECT task, due_date FROM tasks WHERE user_id=?", (session_state['user_id'],)):
        tasks.append(row)

for task in tasks:
    calendar_data.append({
        'title': task[0],
        'start': task[1],
        'backgroundColor': '#3788d8',
        'borderColor': '#3788d8',
        'editable': True,
        'allDay': True
    })

# Veritabanından hedefleri al
goals = []
if 'user_id' in session_state:
    for row in c.execute("SELECT goal, target_date FROM goals WHERE user_id=?", (session_state['user_id'],)):
        goals.append(row)

for goal in goals:
    calendar_data.append({
        'title': goal[0],
        'start': goal[1],
        'backgroundColor': '#28a745',
        'borderColor': '#28a745'
    })

calendar(
    events=calendar_data,
    options={
        'initialView': 'dayGridMonth',
        'initialDate': f'{datetime.now().year}-{datetime.now().month:02d}-01',
        'headerToolbar': {
            'left': 'prev,next today',
            'center': 'title',
            'right': 'dayGridMonth,timeGridWeek,timeGridDay'
        },
        'editable': True,
        'selectable': True,
    }
)

def local_css(file_name):
    with open(file_name, "r") as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

# Kullanıcı kimlik doğrulama
def login_user(username, password):
    c.execute("SELECT * FROM users WHERE username=?", (username,))
    user = c.fetchone()
    if user and bcrypt.checkpw(password.encode('utf-8'), user[2]):
        return user[0]
    return None

def register_user(username, password):
    hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    try:
        c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed))
        conn.commit()
        return c.lastrowid
    except sqlite3.IntegrityError:
        return None

def add_subtask(task_id):
    subtask = st.text_input("Alt görev ekle:")
    if st.button("Alt Görev Ekle"):
        if subtask:
            c.execute('''INSERT INTO subtasks (task_id, subtask, done)
                         VALUES (?, ?, ?)''', (task_id, subtask, False))
            conn.commit()
            st.success(f"Alt görev '{subtask}' başarıyla eklendi!")

def create_recurring_task(task, frequency, end_date):
    current_date = date.today()
    while current_date <= end_date:
        c.execute('''INSERT INTO tasks (user_id, task, done, created_at, priority, tags, due_date)
                     VALUES (?, ?, ?, ?, ?, ?, ?)''',
                  (st.session_state.user_id, task, False, datetime.now(), "Normal", "", current_date))
        if frequency == "Daily":
            current_date += timedelta(days=1)
        elif frequency == "Weekly":
            current_date += timedelta(weeks=1)
        elif frequency == "Monthly":
            current_date = current_date.replace(month=current_date.month % 12 + 1)
    conn.commit()

# Ana uygulama
def main():
    local_css("style.css")
    st.markdown('<h1 class="title">🧠 Gelişmiş ToDo & İkinci Beyin Planlayıcı</h1>', unsafe_allow_html=True)
    
    if 'user_id' not in st.session_state:
        st.session_state.user_id = None

    if st.session_state.user_id is None:
        auth_option = st.radio("Seçenek:", ["Giriş", "Kayıt"])
        if auth_option == "Giriş":
            username = st.text_input("Kullanıcı adı")
            password = st.text_input("Şifre", type="password")
            if st.button("Giriş"):
                user_id = login_user(username, password)
                if user_id:
                    st.session_state.user_id = user_id
                    st.success("Başarıyla giriş yapıldı!")
                    st.experimental_rerun()
                else:
                    st.error("Geçersiz kullanıcı adı veya şifre")
        else:
            username = st.text_input("Kullanıcı adı")
            password = st.text_input("Şifre", type="password")
            if st.button("Kayıt ol"):
                user_id = register_user(username, password)
                if user_id:
                    st.session_state.user_id = user_id
                    st.success("Kayıt başarılı! Giriş yapıldı.")
                    st.experimental_rerun()
                else:
                    st.error("Kullanıcı adı zaten kullanımda")
    else:
        # Sidebar for navigation
        with st.sidebar:
            st.markdown('<h2 class="sidebar-title">Navigasyon</h2>', unsafe_allow_html=True)
            page = st.radio("", ["Görevler", "Notlar", "Bilgi Grafiği", "Analitik", "Pomodoro Zamanlayıcı", "Hedef Takibi", "Takvim"])
            if st.button("Çıkış Yap"):
                st.session_state.user_id = None
                st.experimental_rerun()
        
        if page == "Görevler":
            task_page()
        elif page == "Notlar":
            note_page()
        elif page == "Bilgi Grafiği":
            knowledge_graph_page()
        elif page == "Analitik":
            analytics_page()
        elif page == "Pomodoro Zamanlayıcı":
            pomodoro_page()
        elif page == "Hedef Takibi":
            goal_tracking_page()
        elif page == "Takvim":
            calendar_page()

# Görev yönetimi sayfası
def task_page():
    st.markdown('<h2 class="page-title">📋 Görev Yönetimi</h2>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        new_task = st.text_input("Yeni görev ekle:")
    with col2:
        priority = st.selectbox("Öncelik", ["Düşük", "Orta", "Yüksek"])
    
    tags = st_tags(label="Etiketleri girin:", text="Enter'a basarak daha fazla ekleyin")
    due_date = st.date_input("Son tarih", min_value=date.today())
    
    if st.button("Görev Ekle", key="add_task"):
        if new_task:
            c.execute('''INSERT INTO tasks (user_id, task, done, created_at, priority, tags, due_date)
                         VALUES (?, ?, ?, ?, ?, ?, ?)''',
                      (st.session_state.user_id, new_task, False, datetime.now(), priority, ','.join(tags), due_date))
            conn.commit()
            st.success(f"Görev '{new_task}' başarıyla eklendi!")
    
    recurring_task = st.text_input("Tekrarlanan görev ekle:")
    frequency = st.selectbox("Tekrar sıklığı", ["Daily", "Weekly", "Monthly"])
    end_date = st.date_input("Bitiş tarihi")
    if st.button("Tekrarlanan Görev Ekle"):
        create_recurring_task(recurring_task, frequency, end_date)
    
    # Görevleri filtrele
    filter_priority = st.multiselect("Önceliğe göre filtrele", ["Düşük", "Orta", "Yüksek"])
    filter_tags = st_tags(label="Etiketlere göre filtrele:", text="Enter'a basarak daha fazla ekleyin")
    
    c.execute('''SELECT * FROM tasks WHERE user_id = ? ORDER BY order_index, due_date''', (st.session_state.user_id,))
    tasks = c.fetchall()
    
    filtered_tasks = tasks
    if filter_priority:
        filtered_tasks = [task for task in filtered_tasks if task[4] in filter_priority]
    if filter_tags:
        filtered_tasks = [task for task in filtered_tasks if any(tag in task[6].split(',') for tag in filter_tags)]
    
    # st_draggable'ı kaldırın ve normal bir DataFrame görüntüleme kullanın
    tasks_df = pd.DataFrame(filtered_tasks, columns=['id', 'user_id', 'task', 'done', 'created_at', 'priority', 'tags', 'due_date', 'order_index'])
    st.dataframe(tasks_df)
    
    # Görevleri görüntüle
    for i, task in enumerate(filtered_tasks):
        col1, col2, col3, col4, col5 = st.columns([3, 1, 1, 1, 1])
        
        with col1:
            done = st.checkbox(task[2], task[3], key=f"task_{i}")
            if done != task[3]:
                c.execute("UPDATE tasks SET done = ? WHERE id = ?", (done, task[0]))
                conn.commit()
        
        with col2:
            st.markdown(f'<span class="priority-{task[5].lower()}">{task[5]}</span>', unsafe_allow_html=True)
        
        with col3:
            if st.button("Düzenle", key=f"edit_{i}"):
                edited_task = st.text_input("Görevi düzenle:", task[2], key=f"edit_input_{i}")
                edited_priority = st.selectbox("Önceliği düzenle:", ["Düşük", "Orta", "Yüksek"], index=["Düşük", "Orta", "Yüksek"].index(task[5]), key=f"edit_priority_{i}")
                edited_tags = st_tags(label="Etiketleri düzenle:", text="Enter'a basarak daha fazla ekleyin", value=task[6].split(','), key=f"edit_tags_{i}")
                edited_due_date = st.date_input("Son tarihi düzenle:", task[7], key=f"edit_due_date_{i}")
                if st.button("Kaydet", key=f"save_edit_{i}"):
                    c.execute('''UPDATE tasks SET task = ?, priority = ?, tags = ?, due_date = ? WHERE id = ?''',
                              (edited_task, edited_priority, ','.join(edited_tags), edited_due_date, task[0]))
                    conn.commit()
                    st.success("Görev başarıyla güncellendi!")
                    st.experimental_rerun()
        
        with col4:
            if st.button("Sil", key=f"delete_{i}"):
                c.execute("DELETE FROM tasks WHERE id = ?", (task[0],))
                conn.commit()
                st.experimental_rerun()
        
        with col5:
            if st.button("Alt Görev Ekle", key=f"add_subtask_{i}"):
                add_subtask(task[0])
    
    st.subheader("Yaklaşan Görevler")
    today = date.today()
    c.execute('''SELECT * FROM tasks WHERE user_id = ? AND done = 0 AND due_date >= ? ORDER BY due_date LIMIT 5''',
              (st.session_state.user_id, today))
    upcoming_tasks = c.fetchall()
    
    for task in upcoming_tasks:
        st.write(f"- {task[2]} (Son tarih: {task[7]})")

# Not alma sayfası
def note_page():
    st.markdown('<h2 class="page-title">📝 Notlar</h2>', unsafe_allow_html=True)
    
    new_note_title = st.text_input("Not başlığı:")
    new_note_content = sq.quill_editor(placeholder="Not içeriği...", key="new_note")
    tags = st_tags(label="Etiketleri girin:", text="Enter'a basarak daha fazla ekleyin")
    
    uploaded_file = st.file_uploader("Dosya ekle", type=['pdf', 'docx', 'txt', 'jpg', 'png'])
    
    if st.button("Not Ekle"):
        if new_note_title and new_note_content:
            c.execute('''INSERT INTO notes (user_id, title, content, created_at, tags)
                         VALUES (?, ?, ?, ?, ?)''',
                      (st.session_state.user_id, new_note_title, new_note_content, datetime.now(), ','.join(tags)))
            note_id = c.lastrowid
            conn.commit()
            
            if uploaded_file is not None:
                file_contents = uploaded_file.read()
                c.execute('''INSERT INTO note_attachments (note_id, file_name, file_content)
                             VALUES (?, ?, ?)''', (note_id, uploaded_file.name, file_contents))
                conn.commit()
            
            st.success(f"Not '{new_note_title}' başarıyla eklendi!")
    
    # Notları filtrele
    filter_tags = st_tags(label="Etiketlere göre filtrele:", text="Enter'a basarak daha fazla ekleyin")
    
    c.execute('''SELECT * FROM notes WHERE user_id = ? ORDER BY created_at DESC''', (st.session_state.user_id,))
    notes = c.fetchall()
    
    filtered_notes = notes
    if filter_tags:
        filtered_notes = [note for note in filtered_notes if any(tag in note[5].split(',') for tag in filter_tags)]
    
    # Notları görüntüle
    for i, note in enumerate(filtered_notes):
        with st.expander(note[2]):
            st.markdown(note[3], unsafe_allow_html=True)
            st.write("Etiketler:", ', '.join(note[5].split(',')))
            
            c.execute('''SELECT file_name FROM note_attachments WHERE note_id = ?''', (note[0],))
            attachments = c.fetchall()
            if attachments:
                st.write("Ekler:")
            if st.button("Düzenle", key=f"edit_note_{i}"):
                edited_title = st.text_input("Başlığı düzenle:", note[2], key=f"edit_title_{i}")
                edited_content = st.text_area("İçeriği düzenle:", note[3], key=f"edit_content_{i}")
                edited_tags = st_tags(label="Etiketleri düzenle:", text="Enter'a basarak daha fazla ekleyin", value=note[5].split(','), key=f"edit_note_tags_{i}")
                if st.button("Kaydet", key=f"save_note_{i}"):
                    c.execute('''UPDATE notes SET title = ?, content = ?, tags = ? WHERE id = ?''',
                              (edited_title, edited_content, ','.join(edited_tags), note[0]))
                    conn.commit()
                    st.success("Not başarıyla güncellendi!")
                    st.experimental_rerun()
            if st.button("Sil", key=f"delete_note_{i}"):
                c.execute("DELETE FROM notes WHERE id = ?", (note[0],))
                conn.commit()
                st.experimental_rerun()

# Bilgi grafiği sayfası
def knowledge_graph_page():
    st.markdown('<h2 class="page-title">🕸️ Bilgi Grafiği</h2>', unsafe_allow_html=True)
    
    c.execute('''SELECT task FROM tasks WHERE user_id = ?''', (st.session_state.user_id,))
    tasks = [task[0] for task in c.fetchall()]
    
    c.execute('''SELECT title FROM notes WHERE user_id = ?''', (st.session_state.user_id,))
    notes = [note[0] for note in c.fetchall()]
    
    all_items = tasks + notes
    
    link_type = st.radio("Bağlantı Türü", ["İç", "Dış"])
    
    if link_type == "İç":
        source = st.selectbox("Kaynak", [""] + all_items, key="source_select")
        target = st.selectbox("Hedef", [""] + all_items, key="target_select")
    else:
        source = st.text_input("Kaynak (URL veya isim girin)")
        target = st.selectbox("Hedef", [""] + all_items, key="target_select")
    
    if st.button("Bağlantı Ekle"):
        if source and target and source != target:
            c.execute('''INSERT INTO links (user_id, source, target, type) VALUES (?, ?, ?, ?)''',
                      (st.session_state.user_id, source, target, link_type))
            conn.commit()
            st.success(f"'{source}' ve '{target}' arasındaki bağlantı başarıyla eklendi!")
        else:
            st.error("Lütfen geçerli kaynak ve hedef öğe seçin.")
    
    # Grafik oluştur ve görüntüle
    G = nx.Graph()
    for task in tasks:
        G.add_node(task, color='lightblue', type='task')
    for note in notes:
        G.add_node(note, color='lightgreen', type='note')
    
    c.execute('''SELECT * FROM links WHERE user_id = ?''', (st.session_state.user_id,))
    links = c.fetchall()
    for link in links:
        if link[3] == "İç":
            G.add_edge(link[2], link[3])
        else:
            G.add_node(link[2], color='lightyellow', type='external')
            G.add_edge(link[2], link[3])
    
    pos = nx.spring_layout(G)
    edge_x = []
    edge_y = []
    for edge in G.edges():
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        edge_x.extend([x0, x1, None])
        edge_y.extend([y0, y1, None])

    edge_trace = go.Scatter(
        x=edge_x, y=edge_y,
        line=dict(width=0.5, color='#888'),
        hoverinfo='none',
        mode='lines')

    node_x = []
    node_y = []
    for node in G.nodes():
        x, y = pos[node]
        node_x.append(x)
        node_y.append(y)

    node_trace = go.Scatter(
        x=node_x, y=node_y,
        mode='markers',
        hoverinfo='text',
        marker=dict(
            showscale=True,
            colorscale='YlGnBu',
            reversescale=True,
            color=[],
            size=10,
            colorbar=dict(
                thickness=15,
                title='Node Connections',
                xanchor='left',
                titleside='right'
            ),
            line_width=2))

    node_adjacencies = []
    node_text = []
    for node, adjacencies in enumerate(G.adjacency()):
        node_adjacencies.append(len(adjacencies[1]))
        node_text.append(f'{adjacencies[0]} - # of connections: {len(adjacencies[1])}')

    node_trace.marker.color = node_adjacencies
    node_trace.text = node_text

    fig = go.Figure(data=[edge_trace, node_trace],
                    layout=go.Layout(
                        title='Bilgi Grafiği',
                        titlefont_size=16,
                        showlegend=False,
                        hovermode='closest',
                        margin=dict(b=20,l=5,r=5,t=40),
                        annotations=[ dict(
                            text="Python code: <a href='https://plotly.com/ipython-notebooks/network-graphs/'> https://plotly.com/ipython-notebooks/network-graphs/</a>",
                            showarrow=False,
                            xref="paper", yref="paper",
                            x=0.005, y=-0.002 ) ],
                        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False))
                    )
    
    selected_points = plotly_events(fig)
    if selected_points:
        selected_node = list(G.nodes())[selected_points[0]['pointIndex']]
        st.write(f"Seçilen düğüm: {selected_node}")
        st.write(f"Bağlantılar: {', '.join(G.neighbors(selected_node))}")

# Analitik sayfası
def analytics_page():
    st.markdown('<h2 class="page-title">📊 Analitik</h2>', unsafe_allow_html=True)
    
    # Görev tamamlama oranı
    c.execute('''SELECT COUNT(*) FROM tasks WHERE user_id = ? AND done = 1''', (st.session_state.user_id,))
    completed_tasks = c.fetchone()[0]
    c.execute('''SELECT COUNT(*) FROM tasks WHERE user_id = ?''', (st.session_state.user_id,))
    total_tasks = c.fetchone()[0]
    completion_rate = completed_tasks / total_tasks if total_tasks > 0 else 0
    
    st.subheader("Görev Tamamlama Oranı")
    fig = px.pie(values=[completed_tasks, total_tasks - completed_tasks], names=['Tamamlanan', 'Tamamlanmayan'], hole=0.3)
    st.plotly_chart(fig)
    st.write(f"{completed_tasks} / {total_tasks} görev tamamlandı ({completion_rate:.2%})")
    
    # Zaman içinde görev oluşturma
    c.execute('''SELECT DATE(created_at) as date, COUNT(*) as count 
                 FROM tasks WHERE user_id = ? 
                 GROUP BY DATE(created_at) 
                 ORDER BY date''', (st.session_state.user_id,))
    task_creation_data = c.fetchall()
    
    st.subheader("Zaman İçinde Görev Oluşturma")
    df = pd.DataFrame(task_creation_data, columns=['date', 'count'])
    fig = px.line(df, x='date', y='count')
    st.plotly_chart(fig)
    
    # Zaman içinde not oluşturma
    c.execute('''SELECT DATE(created_at) as date, COUNT(*) as count 
                 FROM notes WHERE user_id = ? 
                 GROUP BY DATE(created_at) 
                 ORDER BY date''', (st.session_state.user_id,))
    note_creation_data = c.fetchall()
    
    st.subheader("Zaman İçinde Not Oluşturma")
    df = pd.DataFrame(note_creation_data, columns=['date', 'count'])
    fig = px.line(df, x='date', y='count')
    st.plotly_chart(fig)
    
    # En çok bağlantılı öğeler
    c.execute('''SELECT source, COUNT(*) as count 
                 FROM links WHERE user_id = ? 
                 GROUP BY source 
                 ORDER BY count DESC 
                 LIMIT 5''', (st.session_state.user_id,))
    most_connected_items = c.fetchall()
    
    if most_connected_items:
        st.subheader("En Çok Bağlantılı Öğeler")
        df = pd.DataFrame(most_connected_items, columns=['item', 'connections'])
        fig = px.bar(df, x='item', y='connections')
        st.plotly_chart(fig)
    
    # Etiket bulutu
    c.execute('''SELECT tags FROM tasks WHERE user_id = ?''', (st.session_state.user_id,))
    task_tags = c.fetchall()
    c.execute('''SELECT tags FROM notes WHERE user_id = ?''', (st.session_state.user_id,))
    note_tags = c.fetchall()
    
    all_tags = [tag for tags in task_tags + note_tags for tag in tags[0].split(',') if tag]
    if all_tags:
        st.subheader("Etiket Bulutu")
        wordcloud = WordCloud(width=800, height=400, background_color='white').generate(" ".join(all_tags))
        fig, ax = plt.subplots()
        ax.imshow(wordcloud, interpolation='bilinear')
        ax.axis('off')
        st.pyplot(fig)

# Pomodoro Zamanlayıcı sayfası
def pomodoro_page():
    st.markdown('<h2 class="page-title">🍅 Pomodoro Zamanlayıcı</h2>', unsafe_allow_html=True)
    
    # Görev seçimi
    c.execute('''SELECT task FROM tasks WHERE user_id = ? AND done = 0''', (st.session_state.user_id,))
    active_tasks = [task[0] for task in c.fetchall()]
    selected_task = st.selectbox("Üzerinde çalışılacak görevi seçin", [""] + active_tasks)
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        if 'pomodoro' not in st.session_state:
            st.session_state.pomodoro = {'active': False, 'start_time': None, 'duration': 25 * 60}
        
        if not st.session_state.pomodoro['active']:
            if st.button("Pomodoro'yu Başlat"):
                if selected_task:
                    st.session_state.pomodoro['active'] = True
                    st.session_state.pomodoro['start_time'] = time.time()
                    st.session_state.pomodoro['current_task'] = selected_task
                else:
                    st.warning("Lütfen Pomodoro'yu başlatmadan önce bir görev seçin.")
        else:
            if st.button("Pomodoro'yu Durdur"):
                st.session_state.pomodoro['active'] = False
                st.session_state.pomodoro['start_time'] = None
                st.session_state.pomodoro['current_task'] = None
    
    with col2:
        st.session_state.pomodoro['duration'] = st.number_input("Süre (dakika)", min_value=1, value=25, step=1) * 60
    
    if st.session_state.pomodoro['active']:
        st.write(f"Mevcut görev: {st.session_state.pomodoro['current_task']}")
        elapsed_time = time.time() - st.session_state.pomodoro['start_time']
        remaining_time = max(st.session_state.pomodoro['duration'] - elapsed_time, 0)
        
        progress = 1 - (remaining_time / st.session_state.pomodoro['duration'])
        st.progress(progress)
        
        mins, secs = divmod(int(remaining_time), 60)
        time_format = '{:02d}:{:02d}'.format(mins, secs)
        st.markdown(f'<h1 class="timer">{time_format}</h1>', unsafe_allow_html=True)
        
        if remaining_time <= 0:
            st.success("Pomodoro tamamlandı! Mola verin.")
            st.session_state.pomodoro['active'] = False
            st.session_state.pomodoro['start_time'] = None
            st.session_state.pomodoro['current_task'] = None
    
    st.subheader("Pomodoro Tekniği")
    st.write("""
    1. Üzerinde çalışılacak bir görev seçin
    2. Zamanlayıcıyı 25 dakikaya (veya seçtiğiniz sreye) ayarlayın
    3. Zamanlayıcı çalana kadar görev üzerinde çalışın
    4. Kısa bir mola verin (5 dakika)
    5. Her 4 Pomodoro'da bir, daha uzun bir mola verin (15-30 dakika)
    """)

# Hedef Takibi sayfası
def goal_tracking_page():
    st.markdown('<h2 class="page-title">🎯 Hedef Takibi</h2>', unsafe_allow_html=True)
    
    new_goal = st.text_input("Yeni bir hedef ekleyin:")
    target_date = st.date_input("Hedef tarihi")
    
    if st.button("Hedef Ekle"):
        if new_goal:
            c.execute('''INSERT INTO goals (user_id, goal, target_date, completed)
                         VALUES (?, ?, ?, ?)''',
                      (st.session_state.user_id, new_goal, target_date, False))
            conn.commit()
            st.success(f"Hedef '{new_goal}' başarıyla eklendi!")
    
    st.subheader("Hedefleriniz")
    c.execute('''SELECT * FROM goals WHERE user_id = ? ORDER BY target_date''', (st.session_state.user_id,))
    goals = c.fetchall()
    
    for i, goal in enumerate(goals):
        col1, col2, col3 = st.columns([3, 1, 1])
        with col1:
            st.write(f"{goal[2]} (Hedef: {goal[3]})")
        with col2:
            if st.button("Tamamla", key=f"complete_goal_{i}"):
                c.execute("UPDATE goals SET completed = ? WHERE id = ?", (True, goal[0]))
                conn.commit()
                st.experimental_rerun()
        with col3:
            if st.button("Sil", key=f"delete_goal_{i}"):
                c.execute("DELETE FROM goals WHERE id = ?", (goal[0],))
                conn.commit()
                st.experimental_rerun()

# Takvim sayfası
def calendar_page():
    st.markdown('<h2 class="page-title">📅 Takvim</h2>', unsafe_allow_html=True)
    
    # Mevcut tarihi al
    today = date.today()
    current_month = today.month
    current_year = today.year

    # Kullanıcının ay ve yıl seçmesine izin ver
    col1, col2 = st.columns(2)
    with col1:
        month = st.selectbox("Ay", range(1, 13), index=current_month-1)
    with col2:
        year = st.selectbox("Yıl", range(current_year-5, current_year+6), index=5)

    # Seçilen ay ve yıl için görevleri ve hedefleri al
    c.execute('''SELECT task, due_date FROM tasks WHERE user_id = ? AND strftime('%Y-%m', due_date) = ?''',
              (st.session_state.user_id, f"{year}-{month:02d}"))
    tasks = c.fetchall()

    c.execute('''SELECT goal, target_date FROM goals WHERE user_id = ? AND strftime('%Y-%m', target_date) = ?''',
              (st.session_state.user_id, f"{year}-{month:02d}"))
    goals = c.fetchall()

    # Takvim verilerini hazırla
    calendar_data = []
    for task in tasks:
        calendar_data.append({
            'title': task[0],
            'start': task[1],
            'backgroundColor': '#3788d8',
            'borderColor': '#3788d8'
        })
    for goal in goals:
        calendar_data.append({
            'title': goal[0],
            'start': goal[1],
            'backgroundColor': '#28a745',
            'borderColor': '#28a745'
        })

    # Takvimi görüntüle
    calendar(
        events=calendar_data,
        options={
            'initialView': 'dayGridMonth',
            'initialDate': f'{year}-{month:02d}-01',
            'headerToolbar': {
                'left': 'prev,next today',
                'center': 'title',
                'right': 'dayGridMonth,timeGridWeek,timeGridDay'
            },
            'editable': True,
            'selectable': True,
        },
        key=f"calendar_{year}_{month}"  # Benzersiz bir anahtar eklendi
    )

    # Seçilen ay için görevleri ve hedefleri listele
    st.subheader(f"{cal.month_name[month]} {year} için Görevler ve Hedefler")
    
    if tasks:
        st.write("Görevler:")
        for task in tasks:
            st.write(f"- {task[0]} (Son tarih: {task[1]})")
    
    if goals:
        st.write("Hedefler:")
        for goal in goals:
            st.write(f"- {goal[0]} (Hedef tarih: {goal[1]})")

if __name__ == "__main__":
    main()


