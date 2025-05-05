import pyodbc

class UserDb:
    def __init__(self):
        self.conn = pyodbc.connect('DRIVER={SQL Server};SERVER=ved;DATABASE=pygaming')
        self.cursor = self.conn.cursor()

    def add_user(self, name, email, password):
        try:
            qry = "INSERT INTO users (u_name, u_email, password, status) VALUES (?, ?, ?, ?)"
            self.cursor.execute(qry, (name, email, password, "active"))  # Default status: active
            self.conn.commit()
            return True
        except Exception as e:
            print("Error:", e)
            return False

    def get_user(self, email, password):
        qry = "SELECT id, u_name, u_email, role, status FROM users WHERE u_email = ? AND password = ?"
        self.cursor.execute(qry, (email, password))
        user = self.cursor.fetchone()
        
        if user:
            if user[4] == "blocked":
                return None  # Blocked users can't log in
            return user
        return None

    def get_all_users(self):
        qry = "SELECT id, u_name, u_email, role, created_at, status FROM users WHERE role = 'user'"
        self.cursor.execute(qry)
        return self.cursor.fetchall()

    def delete_user(self, user_id):
        try:
            qry1 = "DELETE FROM comments WHERE user_id = ?"
            qry2 = "DELETE FROM users WHERE id = ?"
            self.cursor.execute(qry1, (user_id))
            self.cursor.execute(qry2, (user_id,))
            self.conn.commit()
            return True
        except Exception as e:
            print("Error:", e)
            return False

    def update_user_status(self, user_id, status):
        try:
            qry = "UPDATE users SET status = ? WHERE id = ?"
            self.cursor.execute(qry, (status, user_id))
            self.conn.commit()
            return True
        except Exception as e:
            print("Error:", e)
            return False
        
    def add_audit_record(self, user_id, role):
        try:
            qry = "INSERT INTO audit (user_id, login_at, role) VALUES (?, SYSDATETIME(), ?)"
            self.cursor.execute(qry, (user_id, role))
            self.conn.commit()
            return True
        except Exception as e:
            print("Error:", e)
            return False
    def update_logout_time(self, user_id):
        try:
            qry = "UPDATE audit SET logout_at = SYSDATETIME() WHERE user_id = ? AND logout_at IS NULL"
            self.cursor.execute(qry, (user_id,))
            self.conn.commit()
            return True
        except Exception as e:
            print("Error:", e)
            return False
    
    def get_all_usersaudit(self, user_id):
         qry = "SELECT id, login_at, logout_at, role FROM audit WHERE user_id =?"
         self.cursor.execute(qry, (user_id,))
         return self.cursor.fetchall()
     
    def get_all_audit(self):
         qry = """
         SELECT u.u_email, a.login_at, a.logout_at, a.role
         FROM audit a
         JOIN users u ON a.user_id = u.id
         WHERE u.role = 'user'
         ORDER BY a.login_at DESC
         """
         self.cursor.execute(qry)
         return self.cursor.fetchall() 
     
    def add_admin(self, name, email, password, role):
         qry = "INSERT INTO users (u_name, u_email, password, role) VALUES (?, ?, ?, ?)"
         self.cursor.execute(qry, (name, email, password, role))
         self.conn.commit()
 
    def get_user_by_id(self, user_id):
         qry = "SELECT u_email, role, created_at, profile_pic, u_name FROM users WHERE id = ?"
         self.cursor.execute(qry, (int(user_id),))  # Ensure it's an integer
         return self.cursor.fetchone()

    def update_profile_pic(self, user_id, filename):
        try:
            qry = "UPDATE users SET profile_pic = ? WHERE id = ?"
            self.cursor.execute(qry, (filename, user_id))
            self.conn.commit()
            return True
        except Exception as e:
            print("Error:", e)
            return False
        
    def get_game_name(self):
        qry="select * from games"
        self.cursor.execute(qry)
        return self.cursor.fetchall()
      
    def get_leader_record(self, game_id):
        qry = """
            SELECT TOP 1 users.u_name, leaderboard.score
            FROM leaderboard
            JOIN users ON leaderboard.user_id = users.id
            WHERE leaderboard.game_id = ? 
            ORDER BY leaderboard.score DESC
        """
        self.cursor.execute(qry, (game_id,))
        return self.cursor.fetchone()
    
    def get_scores_grouped_by_game(self,user_id):
        qry = f"""
            SELECT g.game_name, u.u_name, s.score, FORMAT(s.played_at, 'dd-MM-yyyy HH:mm') AS played_at
            FROM score s
            JOIN users u ON s.user_id = u.id
            JOIN games g ON s.game_id = g.id
            WHERE s.user_id = {user_id}
            ORDER BY g.game_name, s.score DESC
        """
        self.cursor.execute(qry)
        return self.cursor.fetchall()
    
    def add_post(self, title, content, admin_id):
        try:
            qry = "INSERT INTO posts (title, content, admin_id) VALUES (?, ?, ?)"
            self.cursor.execute(qry, (title, content, admin_id))
            self.conn.commit()
            return True
        except Exception as e:
            print("Error adding post:", e)
            return False
        
    def get_all_posts(self):
        qry = """
            SELECT posts.post_id, posts.title, posts.content, posts.date_posted, users.u_name AS admin_name
            FROM posts
            JOIN users ON posts.admin_id = users.id
            ORDER BY posts.date_posted DESC
        """
        self.cursor.execute(qry)
        return self.cursor.fetchall()
    
    def add_comment(self, post_id, user_id, comment_text):
        try:
            qry = "INSERT INTO comments (post_id, user_id, comment_text) VALUES (?, ?, ?)"
            self.cursor.execute(qry, (post_id, user_id, comment_text))
            self.conn.commit()
            return True
        except Exception as e:
            print("Error adding comment:", e)
            return False
        
    def get_comments_by_post(self, post_id):
        qry = """
            SELECT comments.comment_text, comments.date, users.u_name
            FROM comments
            JOIN users ON comments.user_id = users.id
            WHERE comments.post_id = ?
        ORDER BY comments.date DESC
        """
        self.cursor.execute(qry, (post_id,))
        return self.cursor.fetchall()
    
    def get_live_users(self):
        qry = """
        SELECT users.u_email 
        FROM users
        INNER JOIN audit ON users.id = audit.user_id
        WHERE audit.logout_at IS NULL 
        AND audit.role = 'user'
        """
        self.cursor.execute(qry)
        return self.cursor.fetchall()

    def get_mail(self,email):
        qry = "select * from users where u_email = ?"
        self.cursor.execute(qry, (email))
        user = self.cursor.fetchone()
        return user
    
    def update_password(self,email, new_password):
        self.cursor.execute("UPDATE users SET password = ? WHERE u_email = ?", (new_password, email))
        self.conn.commit()
        #self.conn.close()

    def add_feedback(self, user_id, game_id, content):
        try:
            qry = """
                INSERT INTO feedback (user_id, game_id, content)
                VALUES (?, ?, ?)
            """
            self.cursor.execute(qry, (user_id, game_id, content))
            self.conn.commit()
            return True
        except Exception as e:
            print("Error adding feedback:", e)
            return False
        
    def get_all_feedback(self):
        qry = """
            SELECT f.id, u.u_name, g.game_name, f.content, f.crated_at
            FROM feedback f
            JOIN users u ON f.user_id = u.id
            JOIN games g ON f.game_id = g.id
            ORDER BY f.crated_at DESC
        """
        self.cursor.execute(qry)
        return self.cursor.fetchall()
    
        
    def update_feedback_consideration(self, feedback_ids):
        try:
            placeholders = ','.join('?' for _ in feedback_ids)
            qry = f"UPDATE feedback SET is_considered = 1 WHERE id IN ({placeholders})"
            self.cursor.execute(qry, feedback_ids)
            self.conn.commit()
            return True
        except Exception as e:
            print("Error updating consideration:", e)
            return False
        
    def get_considered_feedback(self):
        qry = """
            SELECT f.id, u.u_name, g.game_name, f.content, f.crated_at
            FROM feedback f
            JOIN users u ON f.user_id = u.id
            JOIN games g ON f.game_id = g.id
            WHERE f.is_considered = 1
            ORDER BY f.crated_at DESC
        """
        self.cursor.execute(qry)
        return self.cursor.fetchall()
    
    def get_user_scores(self, user_id):
        qry = """
            SELECT g.game_name, s.score, s.played_at
            FROM score s
            JOIN games g ON s.game_id = g.id
            WHERE s.user_id = ?
            ORDER BY g.game_name, s.played_at DESC
        """
        self.cursor.execute(qry, (user_id,))
        rows = self.cursor.fetchall()
        scores_by_game = {}
        for game_name, score, played_at in rows:
            scores_by_game.setdefault(game_name, []).append((score, played_at))
        return scores_by_game

    
