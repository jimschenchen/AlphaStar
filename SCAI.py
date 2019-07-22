#-*- coding=utf-8 -*-
"""
一个简单的入门程序 星际2 4.9.3版本测试通过
PvP 对手简单电脑 我方AI只采矿 地图为AutomatonLE
"""
import sc2
# run_game用于启动游戏并指定各项启动参数
# maps指定游戏在哪张地图上运行。Race选择种族，Difficulty选择电脑难度。
from sc2 import run_game, maps, Race, Difficulty
# Bot和Computer分别指你自己写的AI和游戏内置的电脑
from sc2.player import Bot, Computer, Human

from sc2.constants import *

import random

import cv2
import numpy as np



class JimAI(sc2.BotAI):
    """
    这个类就是你要写的AI类，必须要继承sc2.BotAI，很多内置方法都在其中
    """
    def __init__(self):
        self.ITERATIONS_PER_MINUTE = 165
        self.MAX_WORKERS = 80  # 限制最大农民数    

    async def on_step(self, iteration: int):
        """
        on_step这个异步方法必须被重写，再此将会调用你设置的每一步指令。
        """
        self.iteration = iteration
        await self.distribute_workers()
        await self.build_workers()
        await self.build_pylons()
        await self.build_assimilators()
        await self.expand()
        await self.offensive_force_buildings()
        await self.build_offensive_force()        
        await self.attack()
        await self.intel()
        
    async def build_workers(self):
        """
        选择空闲基地建造农民
        noqueue意味着当前建造列表为空
        """
        if len(self.units(NEXUS)) * 24 > len(self.units(PROBE)):  # 每矿农民补满就不补了
            if len(self.units(PROBE)) < self.MAX_WORKERS:
                for nexus in self.units(NEXUS).ready.noqueue:
                    if self.can_afford(PROBE):
                        await self.do(nexus.train(PROBE))        
    
    async def build_pylons(self):
        """
        人口空余不足5时造水晶。
        """
        if self.supply_left < 5 and not self.already_pending(PYLON):
            nexuses = self.units(NEXUS).ready
            if nexuses.exists:
                if self.can_afford(PYLON):
                    await  self.build(PYLON, near=nexuses.first) # near表示建造地点。后期可以用深度学习优化
                    
    async def build_assimilators(self):
        """
        建造气矿
        """
        for nexus in self.units(NEXUS).ready:
            vespenes = self.state.vespene_geyser.closer_than(12.0, nexus)
            for vespene in vespenes:
                if not self.can_afford(ASSIMILATOR):
                    break
                worker = self.select_build_worker(vespene.position)
                if worker is None:
                    break
                if not self.units(ASSIMILATOR).closer_than(1.0, vespene).exists:
                    await self.do(worker.build(ASSIMILATOR, vespene))

    async def expand(self):
        """
        何时扩张 简化版
        基地数量少于3个就立即扩张
        """
        if self.units(NEXUS).amount < 3 and self.can_afford(NEXUS):
            await self.expand_now()
        
    async def offensive_force_buildings(self):
        """
        建造产兵建筑
        """
        print('iterations:', self.iteration / self.ITERATIONS_PER_MINUTE)
        if self.units(PYLON).ready.exists:
            pylon = self.units(PYLON).ready.random
            # 建造BY
            if self.units(GATEWAY).ready.exists and not self.units(CYBERNETICSCORE):
                if self.can_afford(CYBERNETICSCORE) and not self.already_pending(CYBERNETICSCORE):
                    await self.build(CYBERNETICSCORE, near=pylon)
            # 建造更多BG
            elif len(self.units(GATEWAY)) < ((self.iteration / self.ITERATIONS_PER_MINUTE) / 2):  # 粗略计算
                if self.can_afford(GATEWAY) and not self.already_pending(GATEWAY):
                    await self.build(GATEWAY, near=pylon)
            # 这个VS放的早啊
            if self.units(CYBERNETICSCORE).ready.exists:
                if len(self.units(STARGATE)) < ((self.iteration / self.ITERATIONS_PER_MINUTE) / 2) and len(self.units(STARGATE)) <= 2:
                    if self.can_afford(STARGATE) and not self.already_pending(STARGATE):
                        await self.build(STARGATE, near=pylon)


    async def build_offensive_force(self):
        """
        建造战斗单位
        """
        for gw in self.units(GATEWAY).ready.noqueue:
            if not self.units(STALKER).amount > self.units(VOIDRAY).amount:  # 粗略判断
                if self.can_afford(STALKER) and self.supply_left > 0:
                    await self.do(gw.train(STALKER))
    
        for sg in self.units(STARGATE).ready.noqueue:
            if self.can_afford(VOIDRAY) and self.supply_left > 0:
                await self.do(sg.train(VOIDRAY))
                
                
    def find_target(self, state):
        """
        寻找敌方单位
        注意这个函数不是异步的，不用加async
        """
        if len(self.known_enemy_units) > 0:
            return random.choice(self.known_enemy_units)
        elif len(self.known_enemy_structures) > 0:
            return random.choice(self.known_enemy_structures)
        else:
            return self.enemy_start_locations[0]
        
    async def attack(self):
        if self.units(STALKER).amount > 8 and self.units(VOIDRAY).amount > 5:
            for s in self.units(STALKER).idle:
                await self.do(s.attack(self.find_target(self.state)))
            for v in self.units(VOIDRAY).idle:
                await self.do(v.attack(self.find_target(self.state)))
    
        if self.units(STALKER).amount > 3 or self.units(VOIDRAY).amount > 1:
            if len(self.known_enemy_units) > 0:
                for s in self.units(STALKER).idle:
                    await self.do(s.attack(random.choice(self.known_enemy_units)))
                
                for v in self.units(VOIDRAY).idle:
                    await self.do(v.attack(random.choice(self.known_enemy_units)))
                    
    async def intel(self):
        """
        原作者随便起的名字，你也可以起名为AMD_YES
        该函数将游戏运行过程可视化
        """
        print('dir:', dir(self))  # 你总是可以使用dir命令来获取帮助，也可以直接看源码
        game_data = np.zeros((self.game_info.map_size[1], self.game_info.map_size[0], 3), np.uint8)  # 反转图片像素
        # 画出每个基地的位置
        for nexus in self.units(NEXUS):
            nex_pos = nexus.position
            cv2.circle(game_data, (int(nex_pos[0]), int(nex_pos[1])),
                           10, (0, 255, 0), -1)  # 10代表尺寸,三坐标代表RGB,-1代表描边线宽
    
        # 转换坐标
        flipped = cv2.flip(game_data, 0)  # 翻转
        resized = cv2.resize(flipped, dsize=None, fx=2, fy=2)
        cv2.imshow('Intel', resized)
        cv2.waitKey(1)  # 1ms                    


def main():
    run_game(maps.get("AutomatonLE"), [
        #Human(Race.Terran),
        Bot(Race.Protoss, JimAI()),
        Computer(Race.Protoss, Difficulty.Hard)
        ], realtime=False) 


if __name__ == '__main__':
    main()