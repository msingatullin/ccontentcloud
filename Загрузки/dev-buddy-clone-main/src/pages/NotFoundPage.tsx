import React from 'react'
import { Link } from 'react-router-dom'

function NotFoundPage() {
  return (
    <div className="container mx-auto p-4 text-center">
      <h1 className="text-4xl font-bold">404</h1>
      <p className="mt-4 text-xl">Страница не найдена</p>
      <Link to="/" className="mt-4 inline-block text-blue-500 hover:underline">
        Вернуться на главную
      </Link>
    </div>
  )
}

export default NotFoundPage
