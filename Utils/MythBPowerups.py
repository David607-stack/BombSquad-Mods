import bs                   #Created By MythB # http://github.com/MythB
import random
import bsPowerup
import bsUtils
import weakref
import bsInternal
from bsPowerup import PowerupMessage, PowerupAcceptMessage, _TouchedMessage, PowerupFactory, Powerup

defaultPowerupInterval = 8000
gPowerupWearOffTime = 20000
gMythBPowerUpsWearOffTime = 12000

class NewPowerupFactory(PowerupFactory):
    def __init__(self):
        self._lastPowerupType = None

        self.model = bs.getModel("powerup")
        self.modelSimple = bs.getModel("powerupSimple")

        self.texBomb = bs.getTexture("powerupBomb")
        self.texPunch = bs.getTexture("powerupPunch")
        self.texIceBombs = bs.getTexture("powerupIceBombs")
        self.texStickyBombs = bs.getTexture("powerupStickyBombs")
        self.texShield = bs.getTexture("powerupShield")
        self.texImpactBombs = bs.getTexture("powerupImpactBombs")
        self.texHealth = bs.getTexture("powerupHealth")
        self.texLandMines = bs.getTexture("powerupLandMines")
        self.texCurse = bs.getTexture("powerupCurse")
        self.texSuperStar = bs.getTexture("levelIcon") #for superStar powerup
        self.texSpeed = bs.getTexture("powerupSpeed") #for speed powerup
        self.texIceCube = bs.getTexture("tipTopBGColor") #for iceCube powerup
        self.texSurprise = bs.getTexture("powerupHealth") #for surprise powerup
        self.texMartyrdom = bs.getTexture("achievementCrossHair") #for martyrdom
        self.healthPowerupSound = bs.getSound("healthPowerup")
        self.powerupSound = bs.getSound("powerup01")
        self.powerdownSound = bs.getSound("powerdown01")
        self.dropSound = bs.getSound("boxDrop")
        self.superStarSound = bs.getSound("ooh") #for superstar
        self.speedSound = bs.getSound("shieldUp") #for speed
        self.surpriseSound = bs.getSound("hiss") #for surprise
        self.iceCubeSound = bs.getSound("freeze") #for iceCube
        self.martyrdomSound = bs.getSound("activateBeep") #for martyrdom drop
        self.martyrdomPickSound = bs.getSound("gunCocking") #for martyrdom pick
        self.blockSound = bs.getSound('block') #for blocking
        

        # material for powerups
        self.powerupMaterial = bs.Material()

        # material for anyone wanting to accept powerups
        self.powerupAcceptMaterial = bs.Material()

        # pass a powerup-touched message to applicable stuff
        self.powerupMaterial.addActions(
            conditions=(("theyHaveMaterial",self.powerupAcceptMaterial)),
            actions=(("modifyPartCollision","collide",True),
                     ("modifyPartCollision","physical",False),
                     ("message","ourNode","atConnect",_TouchedMessage())))

        # we dont wanna be picked up
        self.powerupMaterial.addActions(
            conditions=("theyHaveMaterial",
                        bs.getSharedObject('pickupMaterial')),
            actions=( ("modifyPartCollision","collide",False)))

        self.powerupMaterial.addActions(
            conditions=("theyHaveMaterial",
                        bs.getSharedObject('footingMaterial')),
            actions=(("impactSound",self.dropSound,0.5,0.1)))

        self._powerupDist = []
        for p,freq in getDefaultPowerupDistribution():
            for i in range(int(freq)):
                self._powerupDist.append(p)

    def getRandomPowerupType(self, forceType=None, excludeTypes=None):
        if excludeTypes:
            #FIXME bsFootball.py:456
            #FIXME runaround and onslaught !
            excludeTypes.append('superStar')
            excludeTypes.append('speed')
            excludeTypes.append('iceCube')
            excludeTypes.append('surprise')
            excludeTypes.append('martyrdom')
        else:
            excludeTypes = []
        return PowerupFactory.getRandomPowerupType(self, forceType, excludeTypes)


def getDefaultPowerupDistribution():
    return (('tripleBombs',3),#3
            ('iceBombs',3),#3
            ('punch',3),#3
            ('impactBombs',3),#3
            ('landMines',2),#2
            ('stickyBombs',3),#3
            ('shield',2),#2
            ('health',1),#1
            ('curse',1),#1
            ('superStar',1),#1
            ('iceCube',2),#2
            ('surprise',1),#1
            ('martyrdom',2),#2 or 1 maybe
            ('speed',2))#2

class NewPowerup(Powerup):
    def __init__(self,position=(0,1,0),powerupType='tripleBombs',expire=True):
        """
        Create a powerup-box of the requested type at the requested position.

        see bs.Powerup.powerupType for valid type strings.
        """
        bs.Actor.__init__(self)

        factory = self.getFactory()
        self.powerupType = powerupType;
        self._powersGiven = False

        mod = factory.model
        rScl = [1.0]
        if powerupType == 'tripleBombs': tex = factory.texBomb
        elif powerupType == 'punch': tex = factory.texPunch
        elif powerupType == 'iceBombs': tex = factory.texIceBombs
        elif powerupType == 'impactBombs': tex = factory.texImpactBombs
        elif powerupType == 'landMines': tex = factory.texLandMines
        elif powerupType == 'stickyBombs': tex = factory.texStickyBombs
        elif powerupType == 'shield': tex = factory.texShield
        elif powerupType == 'health': tex = factory.texHealth
        elif powerupType == 'curse': tex = factory.texCurse
        elif powerupType == 'martyrdom': tex = factory.texMartyrdom
        elif powerupType == 'superStar':
             tex = factory.texSuperStar
             rScl = [0.1]
        elif powerupType == 'speed':tex = factory.texSpeed
        elif powerupType == 'surprise': tex = factory.texSurprise
        elif powerupType == 'iceCube':
             tex = factory.texIceCube
             rScl = [0.1]
        else: raise Exception("invalid powerupType: "+str(powerupType))

        if len(position) != 3: raise Exception("expected 3 floats for position")
        
        self.node = bs.newNode('prop',
                               delegate=self,
                               attrs={'body':'box',
                                      'position':position,
                                      'model':mod,
                                      'lightModel':factory.modelSimple,
                                      'shadowSize':0.5,
                                      'colorTexture':tex,
                                      'reflection':'powerup',
                                      'reflectionScale':rScl,
                                      'materials':(factory.powerupMaterial,
                                                   bs.getSharedObject('objectMaterial'))})

        # animate in..
        curve = bs.animate(self.node,"modelScale",{0:0,140:1.6,200:1})
        bs.gameTimer(200,curve.delete)

        if expire:
            bs.gameTimer(defaultPowerupInterval-2500,
                         bs.WeakCall(self._startFlashing))
            bs.gameTimer(defaultPowerupInterval-1000,
                         bs.WeakCall(self.handleMessage,bs.DieMessage()))
    
    def _flashBillboard(self,tex,spaz):
        spaz.node.billboardOpacity = 1.0
        spaz.node.billboardTexture = tex
        spaz.node.billboardCrossOut = False
        bs.animate(spaz.node,"billboardOpacity",{0:0.0,100:1.0,400:1.0,500:0.0})

    def _powerUpWearOffFlash(self,tex,spaz):
        if spaz.isAlive():
           spaz.node.billboardTexture = tex
           spaz.node.billboardOpacity = 1.0
           spaz.node.billboardCrossOut = True           
                
    def _startFlashing(self):
        if self.node.exists(): self.node.flashing = True       
      
    def handleMessage(self,m):
        self._handleMessageSanityCheck()

        if isinstance(m,PowerupAcceptMessage):
            factory = self.getFactory()
            if self.powerupType == 'health':
                bs.playSound(factory.healthPowerupSound,3,position=self.node.position)
            bs.playSound(factory.powerupSound,3,position=self.node.position)
            self._powersGiven = True
            self.handleMessage(bs.DieMessage())

        elif isinstance(m,_TouchedMessage):
            if not self._powersGiven:
                node = bs.getCollisionInfo("opposingNode")
                spaz = node.getDelegate()
                if spaz is not None and spaz.exists() and spaz.isAlive(): # pass deadbodies error
                    if self.powerupType == 'superStar':
                       tex = bs.Powerup.getFactory().texSuperStar
                       self._flashBillboard(tex,spaz)
                       def colorChanger():
                           if spaz.isAlive():
                              spaz.node.color = (random.random()*2,random.random()*2,random.random()*2)
                              spaz.node.highlight = (random.random()*2,random.random()*2,random.random()*2)
                       def checkStar(val):
                           self._powersGiven = True
                           if spaz.isAlive(): setattr(spaz.node,'invincible',val)
                           if val and spaz.isAlive():
                              if spaz.node.frozen:
                                 spaz.node.handleMessage(bs.ThawMessage())
                              bs.playSound(bs.Powerup.getFactory().superStarSound,position=spaz.node.position)
                              spaz.colorSet = bs.Timer(100,bs.Call(colorChanger),repeat=True)
                              if spaz._cursed:
                                 spaz._cursed = False
                                    # remove cursed material
                                 factory = spaz.getFactory()
                                 for attr in ['materials', 'rollerMaterials']:
                                     materials = getattr(spaz.node, attr)
                                     if factory.curseMaterial in materials:
                                         setattr(spaz.node, attr,
                                                 tuple(m for m in materials
                                                       if m != factory.curseMaterial))
                                 spaz.node.curseDeathTime = 0
                           if not val and spaz.isAlive():
                              spaz.node.color = spaz.getPlayer().color
                              spaz.node.highlight = spaz.getPlayer().highlight
                              spaz.colorSet = None
                              bs.playSound(bs.Powerup.getFactory().powerdownSound,position=spaz.node.position)
                              spaz.node.billboardOpacity = 0.0
                       checkStar(True)  
                       if self._powersGiven == True :                
                          spaz.node.miniBillboard1Texture = tex
                          t = bs.getGameTime()
                          spaz.node.miniBillboard1StartTime = t
                          spaz.node.miniBillboard1EndTime = t+gMythBPowerUpsWearOffTime
                          spaz._starWearOffTimer = bs.Timer(gMythBPowerUpsWearOffTime,bs.Call(checkStar,False))
                          spaz._starWearOffFlashTimer = bs.Timer(gMythBPowerUpsWearOffTime-2000,bs.WeakCall(self._powerUpWearOffFlash,tex,spaz))
                          self.handleMessage(bs.DieMessage())
                    elif self.powerupType == 'speed':
                     if bs.getActivity()._map.isHockey: #dont give speed if map is already hockey.
                        self.handleMessage(bs.DieMessage(immediate=True))
                     if not bs.getActivity()._map.isHockey:
                        spaz = node.getDelegate()
                        tex = bs.Powerup.getFactory().texSpeed
                        self._flashBillboard(tex,spaz)
                        def checkSpeed(val):
                            self._powersGiven = True
                            if spaz.isAlive(): setattr(spaz.node,'hockey',val)
                            if val and spaz.isAlive():
                               bs.playSound(bs.Powerup.getFactory().speedSound,position=spaz.node.position)
                            if not val and spaz.isAlive():
                               bs.playSound(bs.Powerup.getFactory().powerdownSound,position=spaz.node.position)
                               spaz.node.billboardOpacity = 0.0
                        checkSpeed(True)
                        if self._powersGiven == True :                
                           spaz.node.miniBillboard3Texture = tex
                           t = bs.getGameTime()
                           spaz.node.miniBillboard3StartTime = t
                           spaz.node.miniBillboard3EndTime = t+gMythBPowerUpsWearOffTime
                           spaz._speedWearOffTimer = bs.Timer(gMythBPowerUpsWearOffTime,bs.Call(checkSpeed,False))
                           spaz._speedWearOffFlashTimer = bs.Timer(gMythBPowerUpsWearOffTime-2000,bs.WeakCall(self._powerUpWearOffFlash,tex,spaz))
                           self.handleMessage(bs.DieMessage())
                    elif self.powerupType == 'iceCube':
                        spaz = node.getDelegate()
                        def checkFreezer(val):
                            self._powersGiven = True
                            if spaz.isAlive() and spaz.node.invincible:
                               bs.playSound(bs.Powerup.getFactory().blockSound,position=spaz.node.position)
                            if spaz.isAlive() and not spaz.node.invincible:
                               setattr(spaz,'frozen',val)
                            if val and spaz.isAlive() and not spaz.node.invincible:
                               spaz.node.frozen = 1
                               m = bs.newNode('math', owner=spaz, attrs={ 'input1':(0, 1.3, 0),
                                                                               'operation':'add' })
                               spaz.node.connectAttr('torsoPosition', m, 'input2')
                               opsText = bsUtils.PopupText("Oops!",color=(1,1,1),
                                                                   scale=0.9,
                                                                   offset=(0,-1,0)).autoRetain()
                               m.connectAttr('output', opsText.node, 'position')
                               bs.playSound(bs.Powerup.getFactory().iceCubeSound,position=spaz.node.position)
                            if not val and spaz.isAlive():
                               spaz.node.frozen = 0
                        checkFreezer(True)
                        if self._powersGiven == True :                
                           spaz._iceCubeWearOffTimer = bs.Timer(gMythBPowerUpsWearOffTime,bs.Call(checkFreezer,False))
                           self.handleMessage(bs.DieMessage())
                    elif self.powerupType == 'surprise':
                        self._powersGiven = True
                        spaz = node.getDelegate()
                        if spaz.isAlive():
                           bs.shakeCamera(1)
                           bsUtils.PopupText("Surprise!",color=(1,1,1),
                                                         scale=0.9,
                                                         offset=(0,-1,0),
                                                         position=(spaz.node.position[0],spaz.node.position[1]-1,spaz.node.position[2])).autoRetain()
                           bs.playSound(bs.Powerup.getFactory().surpriseSound,position=spaz.node.position)
                           bs.emitBGDynamics(position=spaz.node.position,
                                             velocity=(0,1,0),
                                             count=random.randrange(30,70),scale=0.5,chunkType='spark')
                           spaz.node.handleMessage("knockout",3000)
                           spaz.node.handleMessage("impulse",spaz.node.position[0],spaz.node.position[1],spaz.node.position[2],
                                                           -spaz.node.velocity[0],-spaz.node.velocity[1],-spaz.node.velocity[2],
                                                           400,400,0,0,-spaz.node.velocity[0],-spaz.node.velocity[1],-spaz.node.velocity[2])
                        if self._powersGiven == True :                                                           
                           self.handleMessage(bs.DieMessage())
                    elif self.powerupType == 'martyrdom':
                        spaz = node.getDelegate()
                        tex = bs.Powerup.getFactory().texMartyrdom
                        self._flashBillboard(tex,spaz)
                        def checkDead(): #FIXME
                         if spaz.hitPoints <= 0 and  ((spaz.lastPlayerHeldBy is not None
                            and spaz.lastPlayerHeldBy.exists()) or (spaz.lastPlayerAttackedBy is not None
                            and spaz.lastPlayerAttackedBy.exists() and bs.getGameTime() - spaz.lastAttackedTime < 4000)):
                            try: spaz.lastDeathPos = spaz.node.position #FIXME
                            except Exception: 
                                spaz.dropss = None
                            else: 
                               if not spaz.lastPlayerAttackedBy == spaz.getPlayer():
                                  dropBomb()
                                  spaz.dropss = None
                        def dropBomb():
                               bs.playSound(bs.Powerup.getFactory().martyrdomSound,position=spaz.lastDeathPos)
                               drop0 = bs.Bomb(position=(spaz.lastDeathPos[0]+0.43,spaz.lastDeathPos[1]+4,spaz.lastDeathPos[2]-0.25),
                                            velocity=(0,-6,0),sourcePlayer=spaz.getPlayer(),#some math for perfect triangle
                                            bombType='sticky').autoRetain()
                               drop1 = bs.Bomb(position=(spaz.lastDeathPos[0]-0.43,spaz.lastDeathPos[1]+4,spaz.lastDeathPos[2]-0.25),
                                            velocity=(0,-6,0),sourcePlayer=spaz.getPlayer(),
                                            bombType='sticky').autoRetain()
                               drop2 = bs.Bomb(position=(spaz.lastDeathPos[0],spaz.lastDeathPos[1]+4,spaz.lastDeathPos[2]+0.5),
                                            velocity=(0,-6,0),sourcePlayer=spaz.getPlayer(),
                                            bombType='sticky').autoRetain()                                       
                        def checkVal(val):
                            self._powersGiven = True
                            if val and spaz.isAlive():
                               m = bs.newNode('math', owner=spaz, attrs={ 'input1':(0, 1.3, 0),
                                                                               'operation':'add' })
                               spaz.node.connectAttr('torsoPosition', m, 'input2')
                               activatedText = bsUtils.PopupText("ACTIVATED",color=(1,1,1),
                                                                   scale=0.7,
                                                                   offset=(0,-1,0)).autoRetain()
                               m.connectAttr('output', activatedText.node, 'position')
                               bs.playSound(bs.Powerup.getFactory().martyrdomPickSound,position=spaz.node.position)
                               spaz.isDropped = True
                               spaz.dropss = bs.Timer(1,bs.Call(checkDead),repeat=True)
                        checkVal(True)
                        if self._powersGiven == True :
                           self.handleMessage(bs.DieMessage())
                    else:
                        node.handleMessage(PowerupMessage(self.powerupType,sourceNode=self.node))
                        
        elif isinstance(m,bs.DieMessage):
            if self.node.exists():
                if (m.immediate):
                    self.node.delete()
                else:
                    curve = bs.animate(self.node,"modelScale",{0:1,100:0})
                    bs.gameTimer(150,self.node.delete)

        elif isinstance(m,bs.OutOfBoundsMessage):
            self.handleMessage(bs.DieMessage())

        elif isinstance(m,bs.HitMessage):
            # dont die on punches (thats annoying)
            if m.hitType != 'punch':
                self.handleMessage(bs.DieMessage())
        else:
            bs.Actor.handleMessage(self,m)

bsPowerup.PowerupFactory = NewPowerupFactory
import bs
import random
import bsSpaz
import bsUtils
import settings

defaultPowerupInterval = 8000


class PowerupMessage(object):
    """
    category: Message Classes

    Tell something to get a powerup.
    This message is normally recieved by touching
    a bs.Powerup box.
    
    Attributes:
    
       powerupType
          The type of powerup to be granted (a string).
          See bs.Powerup.powerupType for available type values.

       sourceNode
          The node the powerup game from, or an empty bs.Node ref otherwise.
          If a powerup is accepted, a bs.PowerupAcceptMessage should be sent
          back to the sourceNode to inform it of the fact. This will generally
          cause the powerup box to make a sound and disappear or whatnot.
    """

    def __init__(self, powerupType, sourceNode=bs.Node(None)):
        """
        Instantiate with given values.
        See bs.Powerup.powerupType for available type values.
        """
        self.powerupType = powerupType
        self.sourceNode = sourceNode


class PowerupAcceptMessage(object):
    """
    category: Message Classes

    Inform a bs.Powerup that it was accepted.
    This is generally sent in response to a bs.PowerupMessage
    to inform the box (or whoever granted it) that it can go away.
    """
    pass


class _TouchedMessage(object):
    pass


class PowerupFactory(object):
    """
    category: Game Flow Classes
    
    Wraps up media and other resources used by bs.Powerups.
    A single instance of this is shared between all powerups
    and can be retrieved via bs.Powerup.getFactory().

    Attributes:

       model
          The bs.Model of the powerup box.

       modelSimple
          A simpler bs.Model of the powerup box, for use in shadows, etc.

       texBox
          Triple-bomb powerup bs.Texture.

       texPunch
          Punch powerup bs.Texture.

       texIceBombs
          Ice bomb powerup bs.Texture.

       texStickyBombs
          Sticky bomb powerup bs.Texture.

       texShield
          Shield powerup bs.Texture.

       texImpactBombs
          Impact-bomb powerup bs.Texture.

       texHealth
          Health powerup bs.Texture.

       texLandMines
          Land-mine powerup bs.Texture.

       texCurse
          Curse powerup bs.Texture.

       healthPowerupSound
          bs.Sound played when a health powerup is accepted.

       powerupSound
          bs.Sound played when a powerup is accepted.

       powerdownSound
          bs.Sound that can be used when powerups wear off.

       powerupMaterial
          bs.Material applied to powerup boxes.

       powerupAcceptMaterial
          Powerups will send a bs.PowerupMessage to anything they touch
          that has this bs.Material applied.
    """

    def __init__(self):
        """
        Instantiate a PowerupFactory.
        You shouldn't need to do this; call bs.Powerup.getFactory()
        to get a shared instance.
        """

        self._lastPowerupType = None

        self.model = bs.getModel("powerup")
        self.modelSimple = bs.getModel("powerupSimple")

        self.texBomb = bs.getTexture("powerupBomb")
        self.texPunch = bs.getTexture("powerupPunch")
        self.texIceBombs = bs.getTexture("powerupIceBombs")
        self.texStickyBombs = bs.getTexture("powerupStickyBombs")
        self.texShield = bs.getTexture("powerupShield")
        self.texImpactBombs = bs.getTexture("powerupImpactBombs")
        self.texHealth = bs.getTexture("powerupHealth")
        self.texLandMines = bs.getTexture("powerupLandMines")
        self.texCurse = bs.getTexture("powerupCurse")
        self.texMTweaker = bs.getTexture("achievementFlawlessVictory")

        self.healthPowerupSound = bs.getSound("healthPowerup")
        self.powerupSound = bs.getSound("powerup01")
        self.powerdownSound = bs.getSound("powerdown01")
        self.dropSound = bs.getSound("boxDrop")

        # material for powerups
        self.powerupMaterial = bs.Material()

        # material for anyone wanting to accept powerups
        self.powerupAcceptMaterial = bs.Material()

        # pass a powerup-touched message to applicable stuff
        self.powerupMaterial.addActions(
            conditions=(("theyHaveMaterial", self.powerupAcceptMaterial)),
            actions=(("modifyPartCollision", "collide", True),
                     ("modifyPartCollision", "physical", False),
                     ("message", "ourNode", "atConnect", _TouchedMessage())))

        # we dont wanna be picked up
        self.powerupMaterial.addActions(
            conditions=("theyHaveMaterial",
                        bs.getSharedObject('pickupMaterial')),
            actions=(("modifyPartCollision", "collide", False)))

        self.powerupMaterial.addActions(
            conditions=("theyHaveMaterial",
                        bs.getSharedObject('footingMaterial')),
            actions=(("impactSound", self.dropSound, 0.5, 0.1)))

        self._powerupDist = []
        for p, freq in getDefaultPowerupDistribution():
            for i in range(int(freq)):
                self._powerupDist.append(p)

    def getRandomPowerupType(self, forceType=None, excludeTypes=[]):
        """
        Returns a random powerup type (string).
        See bs.Powerup.powerupType for available type values.

        There are certain non-random aspects to this; a 'curse' powerup,
        for instance, is always followed by a 'health' powerup (to keep things
        interesting). Passing 'forceType' forces a given returned type while
        still properly interacting with the non-random aspects of the system
        (ie: forcing a 'curse' powerup will result
        in the next powerup being health).
        """
        if forceType:
            t = forceType
        else:
            # if the last one was a curse, make this one a health to
            # provide some hope
            if self._lastPowerupType == 'curse':
                t = 'health'
            else:
                while True:
                    t = self._powerupDist[
                        random.randint(0, len(self._powerupDist) - 1)]
                    if t not in excludeTypes:
                        break
        self._lastPowerupType = t
        return t


def getDefaultPowerupDistribution():
    return (('tripleBombs', 3),
            ('iceBombs', 2),
            ('punch', 3),
            ('impactBombs', 3),
            ('landMines', 2),
            ('stickyBombs', 3),
            ('shield', 2),
            ('health', 1),
            ('curse', 1),
            ("motionTweaker", 2))


class Powerup(bs.Actor):
    """
    category: Game Flow Classes

    A powerup box.
    This will deliver a bs.PowerupMessage to anything that touches it
    which has the bs.PowerupFactory.powerupAcceptMaterial applied.

    Attributes:

       powerupType
          The string powerup type.  This can be 'tripleBombs', 'punch',
          'iceBombs', 'impactBombs', 'landMines', 'stickyBombs', 'shield',
          'health', or 'curse'.

       node
          The 'prop' bs.Node representing this box.
    """

    def __init__(self, position=(0, 1, 0), powerupType='tripleBombs', expire=True):
        """
        Create a powerup-box of the requested type at the requested position.

        see bs.Powerup.powerupType for valid type strings.
        """

        bs.Actor.__init__(self)

        factory = self.getFactory()
        self.powerupType = powerupType;
        self._powersGiven = False

        mod = factory.model
        mScl = 1
        color = (1, 1, 1)
        self.portal = None
        name = "none"
        if powerupType == 'tripleBombs':
            tex = factory.texBomb
            name = "Trio Bombs"
        elif powerupType == 'punch':
            tex = factory.texPunch
            name = "Ultra Gloves"
        elif powerupType == 'iceBombs':
            tex = factory.texIceBombs
            name = "Icy Bombs"
        elif powerupType == 'impactBombs':
            tex = factory.texImpactBombs
            name = "Impact Bombs"
        elif powerupType == 'landMines':
            tex = factory.texLandMines
            name = "Land Mines"
        elif powerupType == 'stickyBombs':
            tex = factory.texStickyBombs
            name = "Glue Bombs"
        elif powerupType == 'shield':
            tex = factory.texShield
            name = "Ultra Shield"
        elif powerupType == 'health':
            tex = factory.texHealth
            name = "Med-Kit"
        elif powerupType == 'curse':
            tex = factory.texCurse
            name = "Curse?"
        elif powerupType == "motionTweaker":
            tex = factory.texMTweaker
            name = "Motion Tweaker"
        else:
            raise Exception("invalid powerupType: " + str(powerupType))

        if len(position) != 3: raise Exception("expected 3 floats for position")

        self.node = bs.newNode('prop',
                               delegate=self,
                               attrs={'body': 'box',
                                      'position': position,
                                      'model': mod,
                                      'lightModel': factory.modelSimple,
                                      'shadowSize': 0.5,
                                      'colorTexture': tex,
                                      'reflection': 'powerup',
                                      'reflectionScale': [1.0],
                                      'materials': (factory.powerupMaterial, bs.getSharedObject('objectMaterial'))})
        prefixAnim = {0: (1, 0, 0), 250: (1, 1, 0), 250 * 2: (0, 1, 0), 250 * 3: (0, 1, 1), 250 * 4: (1, 0, 1),
                      250 * 5: (0, 0, 1), 250 * 6: (1, 0, 0)}
        color = (random.random(), random.random(), random.random())
        if settings.nameOnPowerUps:
            m = bs.newNode('math', owner=self.node, attrs={'input1': (0, 0.7, 0), 'operation': 'add'})
            self.node.connectAttr('position', m, 'input2')
            self.nodeText = bs.newNode('text',
                                       owner=self.node,
                                       attrs={'text': str(name),
                                              'inWorld': True,
                                              'shadow': 1.0,
                                              'flatness': 1.0,
                                              'color': color,
                                              'scale': 0.0,
                                              'hAlign': 'center'})
            m.connectAttr('output', self.nodeText, 'position')
            bs.animate(self.nodeText, 'scale', {0: 0, 140: 0.016, 200: 0.01})
            bsUtils.animateArray(self.nodeText, 'color', 3, prefixAnim, True)
            bs.emitBGDynamics(position=self.nodeText.position, velocity=self.node.position, count=10, scale=0.4,
                              spread=0.01, chunkType='sweat')

        if settings.discoLightsOnPowerUps:
            self.nodeLight = bs.newNode('light',
                                        attrs={'position': self.node.position,
                                               'color': color,
                                               'radius': 0.05,
                                               'volumeIntensityScale': 0.03})
            self.node.connectAttr('position', self.nodeLight, 'position')
            bsUtils.animateArray(self.nodeLight, 'color', 3, prefixAnim, True)

        if settings.shieldOnPowerUps:
            self.nodeShield = bs.newNode('shield', owner=self.node, attrs={'color': color,
                                                                           'position': (
                                                                               self.node.position[0],
                                                                               self.node.position[1],
                                                                               self.node.position[2] + 0.5),
                                                                           'radius': 0.8})
            self.node.connectAttr('position', self.nodeShield, 'position')
            bsUtils.animateArray(self.nodeShield, 'color', 3, prefixAnim, True)

        # animate in..
        curve = bs.animate(self.node, "modelScale", {0: 0, 140: 1.6, 200: mScl})
        bs.gameTimer(200, curve.delete)

        if expire:
            bs.gameTimer(defaultPowerupInterval - 2500,
                         bs.WeakCall(self._startFlashing))
            bs.gameTimer(defaultPowerupInterval - 1000,
                         bs.WeakCall(self.handleMessage, bs.DieMessage()))


    @classmethod
    def getFactory(cls):
        """
        Returns a shared bs.PowerupFactory object, creating it if necessary.
        """
        activity = bs.getActivity()
        if activity is None: raise Exception("no current activity")
        try:
            return activity._sharedPowerupFactory
        except Exception:
            f = activity._sharedPowerupFactory = PowerupFactory()
            return f

    def _startFlashing(self):
        if self.node.exists(): self.node.flashing = True

    def handleMessage(self, msg):
        self._handleMessageSanityCheck()

        if isinstance(msg, PowerupAcceptMessage):
            factory = self.getFactory()
            if self.powerupType == 'health':
                bs.playSound(factory.healthPowerupSound, 3,
                             position=self.node.position)
            bs.playSound(factory.powerupSound, 3, position=self.node.position)
            self._powersGiven = True
            self.handleMessage(bs.DieMessage())

        elif isinstance(msg, _TouchedMessage):
            if not self._powersGiven:
                node = bs.getCollisionInfo("opposingNode")
                if node is not None and node.exists():
                    if self.powerupType == "motionTweaker":
                        bs.getSharedObject('globals').slowMotion = bs.getSharedObject('globals').slowMotion is False
                        self._powersGiven = True
                        self.handleMessage(bs.DieMessage())
                    else:
                        node.handleMessage(PowerupMessage(self.powerupType, sourceNode=self.node))

        elif isinstance(msg, bs.DieMessage):
            if self.node.exists():
                if (msg.immediate):
                    self.node.delete()
                else:
                    curve = bs.animate(self.node, "modelScale", {0: 1, 100: 0})
                    bs.gameTimer(100, self.node.delete)
            if self.nodeLight.exists():
                self.nodeLight.delete()

        elif isinstance(msg, bs.OutOfBoundsMessage):
            self.handleMessage(bs.DieMessage())

        elif isinstance(msg, bs.HitMessage):
            # dont die on punches (that's annoying)
            if msg.hitType != 'punch':
                self.handleMessage(bs.DieMessage())
        else:
# Made by Fire Head
nameOnPowerUps = True  # Whether or not to show the powerup's name on top of powerups

shieldOnPowerUps = True  # Whether or not to add shield on powerups

discoLightsOnPowerUps = True  # Whether or not to show disco lights on powerup's location
