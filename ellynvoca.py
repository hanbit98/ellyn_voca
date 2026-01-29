import tkinter as tk
from tkinter import messagebox
import csv
import random
import re

class VocabQuizApp:
    def __init__(self, root):
        self.root = root
        self.root.title("둘째의 단어 시험 (20문제 완전 정복)")
        self.root.geometry("900x600")
        
        # 데이터 저장소
        self.all_data = []      # CSV 전체 데이터
        self.lesson_list = []   # 레슨 목록
        self.quiz_queue = []    # 현재 출제될 문제 리스트 (총 20개)
        
        # 상태 변수
        self.current_question = None
        self.score = 0
        self.current_idx = 0    # 현재 몇 번째 문제인지
        self.total_q = 0        # 총 문제 수
        self.state = "waiting_answer" # 입력대기(waiting_answer) <-> 다음문제대기(waiting_next)
        
        # 화면 프레임 정의
        self.frame_start = tk.Frame(self.root)
        self.frame_quiz = tk.Frame(self.root)
        self.frame_result = tk.Frame(self.root)
        
        # 데이터 로드
        self.load_data("vocab.csv")
        
        # UI 구성
        self.setup_start_screen()
        self.setup_quiz_screen()
        self.setup_result_screen()
        
        # 첫 화면 보여주기
        self.show_frame("start")

    def load_data(self, filename):
        try:
            with open(filename, 'r', encoding='utf-8-sig') as f:
                reader = csv.reader(f)
                header = next(reader) # 헤더 건너뛰기
                
                lessons = set()
                
                for row in reader:
                    # 빈 줄 제외 및 열 개수 확인
                    if len(row) >= 6:
                        # A:Lesson(0), B:No(1), C:Word(2), D:Part(3), E:Meaning(4), F:Example(5)
                        item = {
                            'lesson': row[0].strip(),
                            'word': row[2].strip(),
                            'pos': row[3].strip(),
                            'meaning': row[4].strip(),
                            'example': row[5].strip()
                        }
                        self.all_data.append(item)
                        lessons.add(item['lesson'])
                
                self.lesson_list = sorted(list(lessons))
                
        except FileNotFoundError:
            messagebox.showerror("오류", "vocab.csv 파일을 찾을 수 없습니다.")
            self.root.destroy()
        except Exception as e:
            messagebox.showerror("오류", f"데이터 로드 중 문제 발생: {e}")
            self.root.destroy()

    def show_frame(self, frame_name):
        """화면 전환용 함수"""
        self.frame_start.pack_forget()
        self.frame_quiz.pack_forget()
        self.frame_result.pack_forget()
        
        if frame_name == "start":
            self.frame_start.pack(fill="both", expand=True)
            self.listbox_lesson.focus_set()
        elif frame_name == "quiz":
            self.frame_quiz.pack(fill="both", expand=True)
            self.entry_answer.focus_set()
        elif frame_name == "result":
            self.frame_result.pack(fill="both", expand=True)
            self.btn_restart.focus_set()

    # ------------------ 1. 시작 화면 ------------------
    def setup_start_screen(self):
        tk.Label(self.frame_start, text="시험 볼 레슨을 선택하세요", font=("Malgun Gothic", 24, "bold")).pack(pady=50)

        # 레슨 목록 리스트박스
        self.listbox_lesson = tk.Listbox(self.frame_start, font=("Arial", 16), height=8, selectmode="single")
        self.listbox_lesson.pack(pady=10, padx=100, fill="x")
        
        for lesson in self.lesson_list:
            self.listbox_lesson.insert(tk.END, lesson)
            
        if self.lesson_list:
            self.listbox_lesson.select_set(0)

        btn_start = tk.Button(self.frame_start, text="시험 시작 (Enter)", font=("Malgun Gothic", 16), 
                              bg="#4a90e2", fg="white", command=self.start_quiz)
        btn_start.pack(pady=30, ipadx=20, ipady=10)

        # 엔터키 바인딩
        self.frame_start.bind('<Return>', lambda e: self.start_quiz())
        self.listbox_lesson.bind('<Return>', lambda e: self.start_quiz())

    def start_quiz(self):
        selection = self.listbox_lesson.curselection()
        if not selection:
            return
            
        selected_lesson = self.listbox_lesson.get(selection[0])
        
        # 선택된 레슨의 단어들 추출
        lesson_words = [item for item in self.all_data if item['lesson'] == selected_lesson]
        
        if not lesson_words:
            messagebox.showinfo("알림", "선택한 레슨에 단어가 없습니다.")
            return

        # 문제 생성 (Type A: 뜻, Type B: 예문) -> 총 20문제
        self.quiz_queue = []
        
        for item in lesson_words:
            # Type A: 뜻 보고 단어 쓰기
            self.quiz_queue.append({
                'type': 'A',
                'question': item['meaning'],
                'answer': item['word'],
                'hint': item['pos'],
                'original': item
            })
            
            # Type B: 예문 빈칸 채우기
            # 정규식으로 단어(대소문자 무시) 찾아서 빈칸 만들기
            pattern = re.compile(re.escape(item['word']), re.IGNORECASE)
            hidden_example = pattern.sub("______", item['example'])
            
            self.quiz_queue.append({
                'type': 'B',
                'question': hidden_example,
                'answer': item['word'],
                'hint': item['pos'],
                'original': item
            })
            
        # 문제 섞기
        random.shuffle(self.quiz_queue)
        
        # 초기화
        self.score = 0
        self.current_idx = 0
        self.total_q = len(self.quiz_queue)
        
        # 퀴즈 화면으로 이동
        self.show_frame("quiz")
        self.load_question()

    # ------------------ 2. 퀴즈 화면 ------------------
    def setup_quiz_screen(self):
        # 상단 진행바
        self.lbl_progress = tk.Label(self.frame_quiz, text="", font=("Arial", 14), fg="gray")
        self.lbl_progress.pack(pady=20)

        # 문제 유형
        self.lbl_type = tk.Label(self.frame_quiz, text="", font=("Malgun Gothic", 14, "bold"), fg="#333")
        self.lbl_type.pack(pady=5)

        # 문제 텍스트
        self.lbl_question = tk.Label(self.frame_quiz, text="", font=("Arial", 20), wraplength=800, justify="center")
        self.lbl_question.pack(pady=30, padx=20)
        
        # 힌트
        self.lbl_hint = tk.Label(self.frame_quiz, text="", font=("Arial", 14, "italic"), fg="blue")
        self.lbl_hint.pack(pady=5)

        # 입력창
        self.entry_answer = tk.Entry(self.frame_quiz, font=("Arial", 24), justify="center", bg="#f0f8ff")
        self.entry_answer.pack(pady=20, ipady=10, ipadx=10)
        
        # 정답/오답 표시
        self.lbl_result = tk.Label(self.frame_quiz, text="", font=("Malgun Gothic", 18, "bold"))
        self.lbl_result.pack(pady=20)
        
        # 엔터키 바인딩
        self.entry_answer.bind('<Return>', self.process_enter)

    def load_question(self):
        if self.current_idx >= self.total_q:
            self.finish_quiz()
            return
            
        self.current_question = self.quiz_queue[self.current_idx]
        
        # UI 업데이트
        self.lbl_progress.config(text=f"Question {self.current_idx + 1} / {self.total_q}")
        
        if self.current_question['type'] == 'A':
            self.lbl_type.config(text="[문제] 뜻을 보고 단어를 쓰세요")
        else:
            self.lbl_type.config(text="[문제] 빈칸에 들어갈 단어를 쓰세요")
            
        self.lbl_question.config(text=self.current_question['question'])
        self.lbl_hint.config(text=f"({self.current_question['hint']})")
        
        # 입력창 초기화
        self.entry_answer.delete(0, tk.END)
        self.lbl_result.config(text="")
        self.entry_answer.config(bg="#f0f8ff") # 배경색 원래대로
        
        self.state = "waiting_answer"

    def process_enter(self, event):
        if self.state == "waiting_answer":
            self.check_answer()
        elif self.state == "waiting_next":
            self.current_idx += 1
            self.load_question()

    def check_answer(self):
        user_input = self.entry_answer.get().strip()
        correct_word = self.current_question['answer']
        
        if user_input.lower() == correct_word.lower():
            self.lbl_result.config(text="정답입니다! (O)", fg="green")
            self.entry_answer.config(bg="#e6fffa") # 초록빛 배경
            self.score += 1
        else:
            self.lbl_result.config(text=f"틀렸습니다. 정답: {correct_word}", fg="red")
            self.entry_answer.config(bg="#ffe6e6") # 붉은빛 배경
            
        self.state = "waiting_next"

    # ------------------ 3. 결과 화면 ------------------
    def setup_result_screen(self):
        tk.Label(self.frame_result, text="시험 종료!", font=("Malgun Gothic", 30, "bold")).pack(pady=50)
        
        self.lbl_final_score = tk.Label(self.frame_result, text="", font=("Malgun Gothic", 24), fg="blue")
        self.lbl_final_score.pack(pady=20)
        
        self.btn_restart = tk.Button(self.frame_result, text="다시 시작하기 (Enter)", font=("Malgun Gothic", 16),
                                     bg="#4a90e2", fg="white", command=lambda: self.show_frame("start"))
        self.btn_restart.pack(pady=40, ipadx=20, ipady=10)
        
        self.frame_result.bind('<Return>', lambda e: self.show_frame("start"))

    def finish_quiz(self):
        self.lbl_final_score.config(text=f"총점: {self.score} / {self.total_q} 점")
        self.show_frame("result")

if __name__ == "__main__":
    root = tk.Tk()
    app = VocabQuizApp(root)
    root.mainloop()