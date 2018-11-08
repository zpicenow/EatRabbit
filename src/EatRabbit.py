# coding=utf-8
import random, sys, time, math, pygame
from pygame.locals import *

FPS = 30 # 每秒钟更新屏幕的帧数
WINWIDTH = 640 # 游戏窗口的宽
WINHEIGHT = 480 # 游戏窗口的高
HALF_WINWIDTH = int(WINWIDTH / 2)
HALF_WINHEIGHT = int(WINHEIGHT / 2)

GRASSCOLOR = (24, 255, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)

CAMERASLACK = 90     # 中心焦点
MOVERATE = 9         # 玩家移动距离
BOUNCERATE = 6       # 玩家跳的多快
BOUNCEHEIGHT = 30    # 玩家跳的多高
STARTSIZE = 25       # 玩家初始多大
WINSIZE = 200        # 玩家多大能赢
INVULNTIME = 2       # 无敌时间多长
GAMEOVERTIME = 2     # 自动开始时间多长
MAXHEALTH = 3        # 玩家生命数

NUMGRASS = 20        # 游戏窗口有多少草
NUMRABBITS = 30    # 游戏窗口有多少兔子
RABBITMINSPEED = 3 # 兔子速度下限
RABBITMAXSPEED = 7 # 兔子速度上限
DIRCHANGEFREQ = 2    # 每一帧改变方向
LEFT = 'left'
RIGHT = 'right'

"""
这个程序有三个数据结构来表示玩家、敌军兔子和草地背景物体。数据结构是具有下列键的字典：

所有三种数据结构使用的键值：
    'x' - 游戏世界中物体的左边缘坐标（不是屏幕上的像素坐标）
    'y' - 游戏世界中物体的上边缘坐标（不是屏幕上的像素坐标）
    'rect' - PyPrave.Rect对象，表示对象所在屏幕上的位置。
玩家数据结构键值：
    'surface' - PyPosi.Surface对象，存储将被绘制到屏幕上的兔子的图像。
    'facing' - 无论是向左还是向右，都存储玩家所面对的方向。
    'size' - 像素的宽度和高度。（宽度和高度总是相同的。）
    'bounce' - 表示玩家在弹跳时的哪个点。0意味着站立（没有弹跳），直到最大（弹跳的完成）
    'health' - 一个整数，显示玩家在死亡前能被大兔子击中多少次。
敌方兔子结构键值：
    'surface' - PyPosi.Surface对象，存储将被绘制到屏幕上的兔子的图像。
    'movex' - 兔子每帧水平移动多少像素。一个负整数向左移动，正向右移动。
    'movey' - 兔子每帧垂直移动多少像素。一个负整数在向上移动，一个正向下移动。
    'width' - 兔子图像的宽度，以像素为单位
    'height' - 兔子图像的高度，以像素为单位
    'bounce' - 表示敌方在弹跳时的哪个点。0意味着站立（没有弹跳），直到最大（弹跳的完成）
    'bouncerate' - 兔子敏捷程度，越小跳得越快
    'bounceheight' - 兔子反弹的高度（单位是像素）
草数据结构键值：
    'grassImage' - 一个整数，指的是用于这个草对象的抓取器中的PyPoside.Surface对象的索引。
"""

def main():
    global FPSCLOCK, DISPLAYSURF, BASICFONT, L_SQUIR_IMG, R_SQUIR_IMG, GRASSIMAGES

    pygame.init()
    FPSCLOCK = pygame.time.Clock()
    pygame.display.set_icon(pygame.image.load('gameicon.png'))
    DISPLAYSURF = pygame.display.set_mode((WINWIDTH, WINHEIGHT))
    pygame.display.set_caption('贪吃的兔子')
    BASICFONT = pygame.font.SysFont('arial', 32)

    # 加载游戏文件
    L_SQUIR_IMG = pygame.image.load('rabbit.png')
    R_SQUIR_IMG = pygame.transform.flip(L_SQUIR_IMG, True, False)
    GRASSIMAGES = []
    for i in range(1, 5):
        GRASSIMAGES.append(pygame.image.load('grass%s.png' % i))

    while True:
        runGame()


def runGame():
    # 为新游戏开始设置变量
    invulnerableMode = False  # 如果玩家是无敌状态
    invulnerableStartTime = 0 # 无敌状态时间
    gameOverMode = False      # 玩家是否输了
    gameOverStartTime = 0     # 重新开始时间
    winMode = False           # 玩家是否赢了

    # 创建用于保存游戏文本的服务
    gameOverSurf = BASICFONT.render('Game Over', True, WHITE)
    gameOverRect = gameOverSurf.get_rect()
    gameOverRect.center = (HALF_WINWIDTH, HALF_WINHEIGHT)

    winSurf = BASICFONT.render('You have achieved OMEGA rabbit!', True, WHITE)
    winRect = winSurf.get_rect()
    winRect.center = (HALF_WINWIDTH, HALF_WINHEIGHT)

    winSurf2 = BASICFONT.render('(Press "r" to restart.)', True, WHITE)
    winRect2 = winSurf2.get_rect()
    winRect2.center = (HALF_WINWIDTH, HALF_WINHEIGHT + 30)

    # 游戏窗口视野左上角
    camerax = 0
    cameray = 0

    grassObjs = []    # 储存所有草的实体
    rabbitObjs = [] # 储存所有敌方兔子实体
    # 储存玩家兔子实体:
    playerObj = {'surface': pygame.transform.scale(L_SQUIR_IMG, (STARTSIZE, STARTSIZE)),
                 'facing': LEFT,
                 'size': STARTSIZE,
                 'x': HALF_WINWIDTH,
                 'y': HALF_WINHEIGHT,
                 'bounce':0,
                 'health': MAXHEALTH}

    moveLeft  = False
    moveRight = False
    moveUp    = False
    moveDown  = False

    # 游戏开始随即投放背景
    for i in range(10):
        grassObjs.append(makeNewGrass(camerax, cameray))
        grassObjs[i]['x'] = random.randint(0, WINWIDTH)
        grassObjs[i]['y'] = random.randint(0, WINHEIGHT)

    while True: # 游戏主循环
        # 检查
        if invulnerableMode and time.time() - invulnerableStartTime > INVULNTIME:
            invulnerableMode = False

        # 移动所有的兔子
        for sObj in rabbitObjs:
            # 移动所有的兔子并判断
            sObj['x'] += sObj['movex']
            sObj['y'] += sObj['movey']
            sObj['bounce'] += 1
            if sObj['bounce'] > sObj['bouncerate']:
                sObj['bounce'] = 0 # 重设敏捷程度

            # 随机改变方向
            if random.randint(0, 99) < DIRCHANGEFREQ:
                sObj['movex'] = getRandomVelocity()
                sObj['movey'] = getRandomVelocity()
                if sObj['movex'] > 0: # 面向右
                    sObj['surface'] = pygame.transform.scale(R_SQUIR_IMG, (sObj['width'], sObj['height']))
                else: # 面向左
                    sObj['surface'] = pygame.transform.scale(L_SQUIR_IMG, (sObj['width'], sObj['height']))


        # 遍历所有对象是否删除
        for i in range(len(grassObjs) - 1, -1, -1):
            if isOutsideActiveArea(camerax, cameray, grassObjs[i]):
                del grassObjs[i]
        for i in range(len(rabbitObjs) - 1, -1, -1):
            if isOutsideActiveArea(camerax, cameray, rabbitObjs[i]):
                del rabbitObjs[i]

        # 草或者兔子不够时及时投放
        while len(grassObjs) < NUMGRASS:
            grassObjs.append(makeNewGrass(camerax, cameray))
        while len(rabbitObjs) < NUMRABBITS:
            rabbitObjs.append(makeNewRabbit(camerax, cameray))

        # 改变屏幕焦点
        playerCenterx = playerObj['x'] + int(playerObj['size'] / 2)
        playerCentery = playerObj['y'] + int(playerObj['size'] / 2)
        if (camerax + HALF_WINWIDTH) - playerCenterx > CAMERASLACK:
            camerax = playerCenterx + CAMERASLACK - HALF_WINWIDTH
        elif playerCenterx - (camerax + HALF_WINWIDTH) > CAMERASLACK:
            camerax = playerCenterx - CAMERASLACK - HALF_WINWIDTH
        if (cameray + HALF_WINHEIGHT) - playerCentery > CAMERASLACK:
            cameray = playerCentery + CAMERASLACK - HALF_WINHEIGHT
        elif playerCentery - (cameray + HALF_WINHEIGHT) > CAMERASLACK:
            cameray = playerCentery - CAMERASLACK - HALF_WINHEIGHT

        # 绘制背景
        DISPLAYSURF.fill(GRASSCOLOR)

        # 绘制草
        for gObj in grassObjs:
            gRect = pygame.Rect( (gObj['x'] - camerax,
                                  gObj['y'] - cameray,
                                  gObj['width'],
                                  gObj['height']) )
            DISPLAYSURF.blit(GRASSIMAGES[gObj['grassImage']], gRect)


        # 绘制敌方兔子
        for sObj in rabbitObjs:
            sObj['rect'] = pygame.Rect( (sObj['x'] - camerax,
                                         sObj['y'] - cameray - getBounceAmount(sObj['bounce'], sObj['bouncerate'], sObj['bounceheight']),
                                         sObj['width'],
                                         sObj['height']) )
            DISPLAYSURF.blit(sObj['surface'], sObj['rect'])


        # 绘制玩家兔子
        flashIsOn = round(time.time(), 1) * 10 % 2 == 1
        if not gameOverMode and not (invulnerableMode and flashIsOn):
            playerObj['rect'] = pygame.Rect( (playerObj['x'] - camerax,
                                              playerObj['y'] - cameray - getBounceAmount(playerObj['bounce'], BOUNCERATE, BOUNCEHEIGHT),
                                              playerObj['size'],
                                              playerObj['size']) )
            DISPLAYSURF.blit(playerObj['surface'], playerObj['rect'])


        # 绘制生命值
        drawHealthMeter(playerObj['health'])

        for event in pygame.event.get(): # 事件处理从循环
            if event.type == QUIT:
                terminate()

            elif event.type == KEYDOWN:
                if event.key in (K_UP, K_w):
                    moveDown = False
                    moveUp = True
                elif event.key in (K_DOWN, K_s):
                    moveUp = False
                    moveDown = True
                elif event.key in (K_LEFT, K_a):
                    moveRight = False
                    moveLeft = True
                    if playerObj['facing'] != LEFT: # 改变玩家大小
                        playerObj['surface'] = pygame.transform.scale(L_SQUIR_IMG, (playerObj['size'], playerObj['size']))
                    playerObj['facing'] = LEFT
                elif event.key in (K_RIGHT, K_d):
                    moveLeft = False
                    moveRight = True
                    if playerObj['facing'] != RIGHT: # 改变玩家大小
                        playerObj['surface'] = pygame.transform.scale(R_SQUIR_IMG, (playerObj['size'], playerObj['size']))
                    playerObj['facing'] = RIGHT
                elif winMode and event.key == K_r:
                    return

            elif event.type == KEYUP:
                # 停止移动
                if event.key in (K_LEFT, K_a):
                    moveLeft = False
                elif event.key in (K_RIGHT, K_d):
                    moveRight = False
                elif event.key in (K_UP, K_w):
                    moveUp = False
                elif event.key in (K_DOWN, K_s):
                    moveDown = False

                # elif event.key == K_ESCAPE:
                #     terminate()

        if not gameOverMode:
            # 移动玩家
            if moveLeft:
                playerObj['x'] -= MOVERATE
            if moveRight:
                playerObj['x'] += MOVERATE
            if moveUp:
                playerObj['y'] -= MOVERATE
            if moveDown:
                playerObj['y'] += MOVERATE

            if (moveLeft or moveRight or moveUp or moveDown) or playerObj['bounce'] != 0:
                playerObj['bounce'] += 1

            if playerObj['bounce'] > BOUNCERATE:
                playerObj['bounce'] = 0 # 重设

            # 是否与敌方兔子发生碰撞
            for i in range(len(rabbitObjs)-1, -1, -1):
                sqObj = rabbitObjs[i]
                if 'rect' in sqObj and playerObj['rect'].colliderect(sqObj['rect']):
                    # 玩家与敌方兔子发生碰撞

                    if sqObj['width'] * sqObj['height'] <= playerObj['size']**2:
                        # 玩家大，吃掉兔子
                        playerObj['size'] += int( (sqObj['width'] * sqObj['height'])**0.2 ) + 1
                        del rabbitObjs[i]

                        if playerObj['facing'] == LEFT:
                            playerObj['surface'] = pygame.transform.scale(L_SQUIR_IMG, (playerObj['size'], playerObj['size']))
                        if playerObj['facing'] == RIGHT:
                            playerObj['surface'] = pygame.transform.scale(R_SQUIR_IMG, (playerObj['size'], playerObj['size']))

                        if playerObj['size'] > WINSIZE:
                            winMode = True # 转化到胜利模式

                    elif not invulnerableMode:
                        # 玩家小，受到伤害
                        invulnerableMode = True
                        invulnerableStartTime = time.time()
                        playerObj['health'] -= 1
                        if playerObj['health'] == 0:
                            gameOverMode = True # 转化到失败模式
                            gameOverStartTime = time.time()
        else:
            # 游戏失败，显示文字
            DISPLAYSURF.blit(gameOverSurf, gameOverRect)
            if time.time() - gameOverStartTime > GAMEOVERTIME:
                return # 结束当前游戏

        # 检查是否胜利
        if winMode:
            DISPLAYSURF.blit(winSurf, winRect)
            DISPLAYSURF.blit(winSurf2, winRect2)

        pygame.display.update()
        FPSCLOCK.tick(FPS)




def drawHealthMeter(currentHealth):
    for i in range(currentHealth): # 绘制生命值，红
        pygame.draw.rect(DISPLAYSURF, RED,   (15, 5 + (10 * MAXHEALTH) - i * 10, 20, 10))
    for i in range(MAXHEALTH): # 绘制生命值，白
        pygame.draw.rect(DISPLAYSURF, WHITE, (15, 5 + (10 * MAXHEALTH) - i * 10, 20, 10), 1)


def terminate():
    pygame.quit()
    sys.exit()


def getBounceAmount(currentBounce, bounceRate, bounceHeight):
    # 返回弹跳的偏移量
    # 敏捷程度越大，弹跳越慢
    # 高度越大，跳的越高
    # 当前值必须小于上限
    return int(math.sin( (math.pi / float(bounceRate)) * currentBounce ) * bounceHeight)

def getRandomVelocity():
    speed = random.randint(RABBITMINSPEED, RABBITMAXSPEED)
    if random.randint(0, 1) == 0:
        return speed
    else:
        return -speed


def getRandomOffCameraPos(camerax, cameray, objWidth, objHeight):
    # 创建焦点视角
    cameraRect = pygame.Rect(camerax, cameray, WINWIDTH, WINHEIGHT)
    while True:
        x = random.randint(camerax - WINWIDTH, camerax + (2 * WINWIDTH))
        y = random.randint(cameray - WINHEIGHT, cameray + (2 * WINHEIGHT))
        # 用随机坐标创建一个ReCt对象并使用CulrDebug（）
        # 确保边缘视角
        objRect = pygame.Rect(x, y, objWidth, objHeight)
        if not objRect.colliderect(cameraRect):
            return x, y


def makeNewRabbit(camerax, cameray):
    sq = {}
    generalSize = random.randint(5, 25)
    multiplier = random.randint(1, 3)
    sq['width']  = (generalSize + random.randint(0, 10)) * multiplier
    sq['height'] = (generalSize + random.randint(0, 10)) * multiplier
    sq['x'], sq['y'] = getRandomOffCameraPos(camerax, cameray, sq['width'], sq['height'])
    sq['movex'] = getRandomVelocity()
    sq['movey'] = getRandomVelocity()
    if sq['movex'] < 0: # 面向左
        sq['surface'] = pygame.transform.scale(L_SQUIR_IMG, (sq['width'], sq['height']))
    else: # 面向右
        sq['surface'] = pygame.transform.scale(R_SQUIR_IMG, (sq['width'], sq['height']))
    sq['bounce'] = 0
    sq['bouncerate'] = random.randint(10, 18)
    sq['bounceheight'] = random.randint(10, 50)
    return sq


def makeNewGrass(camerax, cameray):
    gr = {}
    gr['grassImage'] = random.randint(0, len(GRASSIMAGES) - 1)
    gr['width']  = GRASSIMAGES[0].get_width()
    gr['height'] = GRASSIMAGES[0].get_height()
    gr['x'], gr['y'] = getRandomOffCameraPos(camerax, cameray, gr['width'], gr['height'])
    gr['rect'] = pygame.Rect( (gr['x'], gr['y'], gr['width'], gr['height']) )
    return gr


def isOutsideActiveArea(camerax, cameray, obj):
    # 屏幕越界就返回
    # 半屏的尺寸超越窗口大小
    boundsLeftEdge = camerax - WINWIDTH
    boundsTopEdge = cameray - WINHEIGHT
    boundsRect = pygame.Rect(boundsLeftEdge, boundsTopEdge, WINWIDTH * 3, WINHEIGHT * 3)
    objRect = pygame.Rect(obj['x'], obj['y'], obj['width'], obj['height'])
    return not boundsRect.colliderect(objRect)


if __name__ == '__main__':
    main()

