-- DECIES Platform - Seeds Iniciales
-- Sprint 0 - Día 1

-- Insertar roles básicos
INSERT INTO roles (name, description) 
SELECT 'tutor', 'Profesor o tutor del sistema'
WHERE NOT EXISTS (SELECT 1 FROM roles WHERE name = 'tutor');

INSERT INTO roles (name, description)
SELECT 'student', 'Estudiante del sistema'
WHERE NOT EXISTS (SELECT 1 FROM roles WHERE name = 'student');

-- Insertar usuarios de prueba
INSERT INTO users (email, hashed_password, full_name, role_id)
SELECT 'tutor@decies.test', '$2b$12$LQv3c5yqeJCZ5z9KQv3c5yqeJCZ5z9KQv3c5yqeJCZ5z9KQ', 'Prof. Test Tutor', (SELECT id FROM roles WHERE name = 'tutor')
WHERE NOT EXISTS (SELECT 1 FROM users WHERE email = 'tutor@decies.test');

INSERT INTO users (email, hashed_password, full_name, role_id)
SELECT 'student1@decies.test', '$2b$12$LQv3c5yqeJCZ5z9KQv3c5yqeJCZ5z9KQv3c5yqeJCZ5z9KQ', 'Estudiante Uno', (SELECT id FROM roles WHERE name = 'student')
WHERE NOT EXISTS (SELECT 1 FROM users WHERE email = 'student1@decies.test');

INSERT INTO users (email, hashed_password, full_name, role_id)
SELECT 'student2@decies.test', '$2b$12$LQv3c5yqeJCZ5z9KQv3c5yqeJCZ5z9KQv3c5yqeJCZ5z9KQ', 'Estudiante Dos', (SELECT id FROM roles WHERE name = 'student')
WHERE NOT EXISTS (SELECT 1 FROM users WHERE email = 'student2@decies.test');

-- Insertar asignaturas de prueba
INSERT INTO subjects (name, description, tutor_id)
SELECT 'Matemáticas Básicas', 'Curso de matemáticas nivel básico', (SELECT id FROM users WHERE email = 'tutor@decies.test')
WHERE NOT EXISTS (SELECT 1 FROM subjects WHERE name = 'Matemáticas Básicas');

INSERT INTO subjects (name, description, tutor_id)
SELECT 'Lengua y Literatura', 'Curso de lengua española', (SELECT id FROM users WHERE email = 'tutor@decies.test')
WHERE NOT EXISTS (SELECT 1 FROM subjects WHERE name = 'Lengua y Literatura');

-- Asignar estudiantes a asignaturas
INSERT INTO students (user_id, subject_id)
SELECT (SELECT id FROM users WHERE email = 'student1@decies.test'), (SELECT id FROM subjects WHERE name = 'Matemáticas Básicas')
WHERE NOT EXISTS (SELECT 1 FROM students WHERE user_id = (SELECT id FROM users WHERE email = 'student1@decies.test'));

INSERT INTO students (user_id, subject_id)
SELECT (SELECT id FROM users WHERE email = 'student2@decies.test'), (SELECT id FROM subjects WHERE name = 'Matemáticas Básicas')
WHERE NOT EXISTS (SELECT 1 FROM students WHERE user_id = (SELECT id FROM users WHERE email = 'student2@decies.test'));
