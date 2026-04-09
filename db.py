import  aiosqlite

async def execute_query(query: str, params: tuple = (), commit: bool = True, one: int = 0):
    async with aiosqlite.connect('users.db') as conn:
        async with conn.execute(query, params) as cursor:
            if commit:
                await conn.commit()  # Подтверждаем изменения только при необходимости
            if one == 1:
                return await cursor.fetchone()
            elif one == 2:
                return await cursor.fetchall()
            else:
                pass