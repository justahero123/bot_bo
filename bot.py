import os
import random
import asyncio
import discord
from discord.ext import commands
import yt_dlp

# Cấu hình quyền cho Bố
intents = discord.Intents.default()
intents.message_content = True
intents.members = True # Bắt buộc bật để Bố nhìn thấy người vào server

# Khởi tạo Bot
bot = commands.Bot(command_prefix="!", intents=intents)

# ID kênh thông báo chào mừng
CHANNEL_ID = 697342926421753919

# Cấu hình yt-dlp để tìm nhạc và lấy link âm thanh mượt nhất
YTDL_OPTIONS = {
    'format': 'bestaudio/best',
    'noplaylist': True,
    'default_search': 'ytsearch',
    'quiet': True,
}

FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn',
}

# Sự kiện khi Bố thức dậy thành công và đồng bộ lệnh /
@bot.event
async def on_ready():
    try:
        synced = await bot.tree.sync()
        print(f"🔥 Đã đồng bộ thành công {len(synced)} lệnh / !")
    except Exception as e:
        print(e)
    print(f'🔥 {bot.user.name} đã online và sẵn sàng gáy trong server!')

# Sự kiện tự động chào đón khi có thành viên mới hoặc bot vào server
@bot.event
async def on_member_join(member: discord.Member):
    channel = bot.get_channel(CHANNEL_ID)
    if channel:
        await channel.send(f"Bố chào {member.mention} nhá")

# 1. Lệnh /bo: Gọi Bố
@bot.tree.command(name="bo", description="Gọi Bố ra xem Bố có nhà không!")
async def slash_bo(interaction: discord.Interaction):
    await interaction.response.send_message('Ơi, bố đây con')

# 2. Lệnh /meme: Bắn ảnh meme ngẫu nhiên
@bot.tree.command(name="meme", description="Bốc ngẫu nhiên một chiếc meme từ kho của Bố!")
async def slash_meme(interaction: discord.Interaction):
    folder_path = "./memes"
    if not os.path.exists(folder_path) or not os.listdir(folder_path):
        await interaction.response.send_message('Kho meme của Bố đang trống! Mày chưa cho Bố ăn ảnh kìa.')
        return
    
    all_images = os.listdir(folder_path)
    random_image = random.choice(all_images)
    image_path = os.path.join(folder_path, random_image)
    
    file = discord.File(image_path)
    await interaction.response.send_message(content='meme nè con trai', file=file)

# 3. Lệnh /joke: Kể chuyện cười nhạt
@bot.tree.command(name="joke", description="Nghe Bố phun châu nhả ngọc với một câu dad-joke!")
async def slash_joke(interaction: discord.Interaction):
    joke_file = "jokes.txt"
    if not os.path.exists(joke_file):
        await interaction.response.send_message('Chưa thấy file jokes.txt đâu con ơi!')
        return
    
    with open(joke_file, "r", encoding="utf-8") as f:
        jokes = f.readlines()
    
    if not jokes:
        await interaction.response.send_message('Hết chuyện để kể rồi con ơi!')
        return
    
    random_joke = random.choice(jokes).strip()
    await interaction.response.send_message(f'bố bảo: "{random_joke}"')

# 4. Lệnh /chui @user: Bố mắng yêu một ai đó trong server
@bot.tree.command(name="chui", description="Bố sẽ ra tay dạy dỗ một thành viên ngứa đòn trong server!")
@discord.app_commands.describe(user="Chọn người mà Bố cần dạy dỗ")
async def slash_chui(interaction: discord.Interaction, user: discord.Member):
    chui_file = "chui.txt"
    if not os.path.exists(chui_file):
        await interaction.response.send_message('Chưa thấy file chui.txt đâu con ơi!')
        return
    
    with open(chui_file, "r", encoding="utf-8") as f:
        lines = f.readlines()
    
    if not lines:
        await interaction.response.send_message('Kho chửi đang trống con ơi!')
        return
    
    random_line = random.choice(lines).strip()
    final_message = random_line.replace("{target}", user.mention)
    await interaction.response.send_message(final_message)

# 5. Lệnh /del [số_lượng]: Dọn dẹp chiến trường (Chỉ Admin / Người có quyền)
@bot.tree.command(name="del", description="Dọn dẹp chiến trường, xóa nhanh số lượng tin nhắn (Chỉ Admin mới dùng được)!")
@discord.app_commands.describe(so_luong="Nhập số lượng tin nhắn cần xóa")
@discord.app_commands.checks.has_permissions(manage_messages=True)
async def slash_del(interaction: discord.Interaction, so_luong: int):
    deleted = await interaction.channel.purge(limit=so_luong + 1)
    await interaction.response.send_message(f'🧹 Bố đã dọn sạch {len(deleted) - 1} tin nhắn cho con trai!', ephemeral=True)

# Bắt lỗi khi thành viên không đủ quyền dùng lệnh /del
@slash_del.error
async def slash_del_error(interaction: discord.Interaction, error: discord.app_commands.AppCommandError):
    if isinstance(error, discord.app_commands.MissingPermissions):
        await interaction.response.send_message("con không có thẩm quyền để xoá tin nhắn này con zai ạ", ephemeral=True)
    else:
        await interaction.response.send_message(f"Có lỗi xảy ra rồi con ơi: `{error}`", ephemeral=True)

# 6. Lệnh /play [nhac]: Tự động vào phòng voice và phát nhạc
@bot.tree.command(name="play", description="Bố vào phòng voice phát nhạc từ tên bài hát hoặc link YouTube!")
@discord.app_commands.describe(nhac="Nhập tên bài hát hoặc dán link YouTube vào đây")
async def slash_play(interaction: discord.Interaction, nhac: str):
    if not interaction.user.voice:
        await interaction.response.send_message("Mày phải chui vào một phòng Voice trước thì Bố mới biết đường vào hát chứ!")
        return

    await interaction.response.defer()

    voice_channel = interaction.user.voice.channel
    voice_client = interaction.guild.voice_client

    try:
        if voice_client is None:
            voice_client = await voice_channel.connect(timeout=10.0, reconnect=False)
        elif voice_client.channel != voice_channel:
            await voice_client.move_to(voice_channel)
    except Exception as e:
        await interaction.followup.send(f"❌ Bố không chui vào phòng Voice được: `{e}`")
        return

    try:
        search_query = nhac if nhac.startswith("http") else f"ytsearch1:{nhac}"
        with yt_dlp.YoutubeDL(YTDL_OPTIONS) as ydl:
            info = await asyncio.to_thread(ydl.extract_info, search_query, download=False)
            if 'entries' in info:
                if not info['entries']:
                    await interaction.followup.send("Tìm đỏ mắt không thấy bài này trên YouTube con ơi!")
                    return
                info = info['entries'][0]
            
            audio_url = info['url']
            title = info.get('title', 'Bài hát không tên')

        if voice_client.is_playing():
            voice_client.stop()

        source = discord.FFmpegPCMAudio(audio_url, **FFMPEG_OPTIONS)
        voice_client.play(source)

        await interaction.followup.send(f"🎵 Bố đang lên nhạc bài: **{title}**")
    except Exception as e:
        await interaction.followup.send(f"❌ Lỗi khi lấy nhạc: `{e}`")

# 7. Lệnh /stop: Dừng nhạc và cho Bố rời phòng voice
@bot.tree.command(name="stop", description="Bảo Bố tắt nhạc và rời khỏi phòng Voice!")
async def slash_stop(interaction: discord.Interaction):
    voice_client = interaction.guild.voice_client
    if voice_client and voice_client.is_connected():
        await voice_client.disconnect()
        await interaction.response.send_message("Bố tắt nhạc đi nghỉ đây!")
    else:
        await interaction.response.send_message("Bố có đang ở trong phòng Voice nào đâu!")

# Token của Bố
TOKEN = "MTU2Mzk2NzkxNTA1MTcxMjU2Mg.GU-ur8._A6JtS3bIdMm5rh74c4Q1geyA8MLaAc5xiFAps"

bot.run(TOKEN)