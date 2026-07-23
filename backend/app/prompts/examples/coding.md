# 编程示例

## Python 示例：简单的 Web API

```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root():
    return {"Hello": "World"}
```

## TypeScript 示例：React Hook

```typescript
import { useState, useEffect } from 'react';

function useDebounce<T>(value: T, delay: number): T {
    const [debouncedValue, setDebouncedValue] = useState<T>(value);
    
    useEffect(() => {
        const handler = setTimeout(() => setDebouncedValue(value), delay);
        return () => clearTimeout(handler);
    }, [value, delay]);
    
    return debouncedValue;
}
```

## SQL 示例：分页查询

```sql
SELECT * FROM users
WHERE status = 1
ORDER BY created_at DESC
LIMIT 20 OFFSET 0;
```