Для доступа к **Yandex Cloud** с использованием **Static Key ID** (статического ключа доступа) вам необходимо создать **Service Account** (сервисный аккаунт) и сгенерировать для него **Static Access Key**.  

### 🔹 **Шаги для получения Static Key ID:**
1. **Войдите в Yandex Cloud Console**  
   - Перейдите в [консоль управления Yandex Cloud](https://console.cloud.yandex.ru/).  

2. **Создайте сервисный аккаунт (если его нет)**  
   - В меню слева выберите **"Service Accounts"** (Сервисные аккаунты).  
   - Нажмите **"Create Service Account"**.  
   - Укажите имя и описание, затем нажмите **"Create"**.  

3. **Назначьте роли сервисному аккаунту**  
   - Перейдите в настройки сервисного аккаунта.  
   - На вкладке **"Roles"** нажмите **"Assign Role"**.  
   - Выберите нужные роли (например, `editor`, `storage.admin` и т. д.).  

4. **Создайте Static Access Key**  
   - В настройках сервисного аккаунта перейдите на вкладку **"API Keys"**.  
   - Нажмите **"Create API Key"** → **"Create Static Access Key"**.  
   - Сохраните **Key ID** и **Secret Key** (Secret Key показывается только один раз!).  

### 🔹 **Где используется Static Key ID?**  
- **Key ID** (`access_key_id`) и **Secret Key** (`secret_access_key`) используются для:  
  - Доступа к **Yandex Object Storage (S3)**.  
  - Авторизации в **Yandex Cloud SDK** (например, для Terraform).  
  - Работы с **CLI и API Yandex Cloud**.  

### 🔹 **Пример использования в AWS CLI (для Yandex Object Storage)**  
Если вы используете **S3-совместимое хранилище**, настройте `~/.aws/credentials`:  
```ini
[yandex]
aws_access_key_id = <ваш Key ID>
aws_secret_access_key = <ваш Secret Key>
```
И укажите эндпоинт:  
```bash
aws --endpoint-url=https://storage.yandexcloud.net s3 ls
```

### ⚠️ **Важно!**  
- **Secret Key** нельзя восстановить — сохраните его в безопасное место.  
- Если ключ утерян, нужно создать новый.  
- Для повышенной безопасности используйте **IAM-токены** или **авторизацию через метаданные** на виртуальных машинах.  

Если вам нужен **IAM-токен** (временный ключ), его можно получить через CLI:  
```bash
yc iam create-token
```
Но для долгосрочного доступа **Static Key** удобнее.  

