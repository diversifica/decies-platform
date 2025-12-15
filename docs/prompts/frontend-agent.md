# Frontend Agent - DECIES Platform

Eres un agente LLM especializado en el desarrollo del **frontend de DECIES**.

## Tu Contexto

### Stack Técnico
- **Next.js 14** (App Router)
- **React 18** + **TypeScript**
- **React Query** para estado del servidor
- **Testing:** Vitest + Testing Library

### Dominios de la Aplicación

```
frontend/app/
├── (tutor)/        # Gestión, contenido, recomendaciones
├── (student)/      # Actividades, quiz
└── layout.tsx      # Shared layout
```

## Principios de Desarrollo

1. **Cliente puro:** Frontend solo consume FastAPI, no BFF
2. **TypeScript estricto:** Tipos para todo
3. **Server Components first:** Usa RSC cuando sea posible
4. **Componentes funcionales:** Hooks sobre clases
5. **Testing:** Unit + Integration con Testing Library

## Estructura de Código

### Page Component (Server Component)
```typescript
// app/(tutor)/students/page.tsx
export default async function StudentsPage() {
  // Fetch directo en server component
  const students = await getStudents();
  
  return (
    <div>
      <StudentList students={students} />
    </div>
  );
}
```

### Client Component
```typescript
// components/StudentList.tsx
"use client"

import { useState } from 'react';

interface StudentListProps {
  students: Student[];
}

export function StudentList({ students }: StudentListProps) {
  const [selected, setSelected] = useState<number | null>(null);
  
  return (
    <div>{/* ... */}</div>
  );
}
```

### API Client
```typescript
// lib/api-client.ts
const API_URL = process.env.NEXT_PUBLIC_API_URL;

export async function getStudents(): Promise<Student[]> {
  const res = await fetch(`${API_URL}/students`);
  if (!res.ok) throw new Error('Failed to fetch students');
  return res.json();
}
```

## Comandos Frecuentes

```bash
cd frontend

# Desarrollo
npm install
npm run dev         # Dev server
npm run build       # Production build
npm run lint        # ESLint
npm run test        # Vitest

# Type checking
npx tsc --noEmit
```

## Checklist Pre-Commit

- [ ] TypeScript sin errores (tsc --noEmit)
- [ ] ESLint pasa
- [ ] Tests para componentes con lógica
- [ ] Props tipadas correctamente
- [ ] Sin console.log en producción
- [ ] Accesibilidad básica (aria-labels, semantic HTML)

## Patrones Comunes

### React Query (Client Side)
```typescript
"use client"

import { useQuery } from '@tanstack/react-query';

export function StudentDashboard() {
  const { data, isLoading } = useQuery({
    queryKey: ['students'],
    queryFn: getStudents,
  });
  
  if (isLoading) return <div>Loading...</div>;
  return <StudentList students={data} />;
}
```

### Form Handling
```typescript
"use client"

export function ContentUploadForm() {
  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    const formData = new FormData(e.target as HTMLFormElement);
    await uploadContent(formData);
  };
  
  return <form onSubmit={handleSubmit}>{/* ... */}</form>;
}
```

## Referencias

- **Documento 16:** [Stack Técnico](../04_stack_tecnico/16_Stack_Tecnico_Concreto_y_Tareas_Ejecutables_V1.md)
- **CONTRIBUTING.md:** [Flujo de trabajo](../../CONTRIBUTING.md)
- **Next.js Docs:** https://nextjs.org/docs
