<h1 align="center">💊 Pyllren</h1>

<p align="center">
  <b>Sistema monolítico moderno para la gestión inteligente de inventario y ventas farmacéuticas</b><br/>
  Optimizando la trazabilidad de lotes, sincronización entre sucursales y control de stock en tiempo real.
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Made%20with-FastAPI-109989?logo=fastapi&logoColor=white" alt="FastAPI"/>
  <img src="https://img.shields.io/badge/Frontend-React-61DAFB?logo=react&logoColor=white" alt="React"/>
  <img src="https://img.shields.io/badge/Database-PostgreSQL-336791?logo=postgresql&logoColor=white" alt="PostgreSQL"/>
  <img src="https://img.shields.io/badge/Cache-Redis-DC382D?logo=redis&logoColor=white" alt="Redis"/>
  <img src="https://img.shields.io/badge/NoSQL-MongoDB-47A248?logo=mongodb&logoColor=white" alt="MongoDB"/>
  <img src="https://img.shields.io/badge/License-MIT-blue.svg" alt="License: MIT"/>
</p>

---

## 🧩 Descripción general

**Pyllren** es una plataforma integral para la **gestión farmacéutica**, construida con una arquitectura **monolítica moderna** que unifica un backend ágil con **FastAPI** y un frontend interactivo con **React**.

El sistema incorpora **hilos concurrentes** para automatizar tareas internas como:
- 🔍 Vigilancia de lotes próximos a vencer.  
- 🔄 Sincronización entre bodegas y sucursales.  
- 💾 Copias de seguridad automáticas.  
- 🧹 Limpieza periódica de datos temporales.  
- ⚡ Precarga de productos populares en caché.  

---

## 🧠 Objetivo del proyecto

Ofrecer una herramienta moderna que garantice la **eficiencia, trazabilidad y rendimiento** en el manejo de inventarios farmacéuticos, apoyada en automatización y procesamiento concurrente para reducir carga operativa y errores humanos.

---

## 🚀 Tecnologías principales

| Capa | Tecnologías |
|------|--------------|
| **Frontend** | React · Tailwind CSS · Framer Motion |
| **Backend** | FastAPI · Python · JWT · Pytest |
| **Bases de datos** | PostgreSQL · Redis · MongoDB |

---

---

## 🧩 Cómo ejecutar

```bash
...
cd backend
uvicorn app.main:app --reload

# Iniciar frontend
cd frontend
npm run dev
