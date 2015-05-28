import maya.cmds as cmds

# FUNCTIONS

def removeUnicode(unicode):
     unicodeString = str(unicode)
     return unicodeString[3:len(unicode)-3]

# Region: transfer anim functions

def findParent(object):
    parent = cmds.listRelatives(object, allParents=True)
    if parent == None:
        return None
    else:
        return removeUnicode(parent)

def collectParents(object):
    parentRelatives = []

    def checkAndAppendParents(object):
        if findParent(object) != None:
            currentParent = findParent(object)
            #print "appending current parent: " + str(currentParent)
            parentRelatives.append(currentParent)
            #print "finding parent: " + str(findParent(currentParent))
            checkAndAppendParents(currentParent)
        else:
            pass

    checkAndAppendParents(object)
    #print str(object) + " parentRelatives: " + str(parentRelatives)
    return parentRelatives

def findConstraints(object):
    foundConstraintsList = cmds.listConnections(object, t="constraint")
    if foundConstraintsList == None:
        uniqueConstraintsList = []
    else:
        uniqueConstraintsList = set(foundConstraintsList)
    constraintsList = []
    # makes constraint list without unicode
    for i in uniqueConstraintsList:
        constraintsList.append(str(i))
    #print str(object) + " constraints list: " + str(constraintsList)
    return constraintsList

def collectIncomingConnections(object):
    listIncomingConnections = cmds.listConnections(object, d=False)
    incomingConnections = []
    if listIncomingConnections != None:
        for i in listIncomingConnections:
              if i == object:
                   pass
              else:
                   incomingConnections.append(str(i))
    else:
        pass
    #print str(object) + " incoming connections: " + str(sorted(set(incomingConnections)))
    return sorted(set(incomingConnections))                                

def findConstraintInfluencers(object):
    foundConstraints = findConstraints(object)
    constraintInfluencers = []
    for i in foundConstraints:
        incomingConnections = collectIncomingConnections(i)
        for c in incomingConnections:
            constraintInfluencers.append(c)
    return sorted(set(constraintInfluencers)) 


def collectTransformInfluencers(object):
     transformInfluencers = []

     def checkDuplicateInfluencers(object):
          duplicates = 0
          for i in transformInfluencers:
              if i == object:
                   duplicates += 1
              else: 
                    pass
          if duplicates > 0:
              return True
          else:
              return False

     def collectInfluencers(object):

         # find constraint connections of object
         constraintInfluencers = findConstraintInfluencers(object)
         for i in constraintInfluencers:
             if checkDuplicateInfluencers(i) == False:
                 transformInfluencers.append(i)
                 collectInfluencers(i)

         # find parent of object
         collectedParents = collectParents(object)
         for i in collectedParents:
             if checkDuplicateInfluencers(i) == False:
                 transformInfluencers.append(i)
                 collectInfluencers(i)

     collectInfluencers(object)
     return sorted(set(transformInfluencers))


# Collect Time Changes/key frame timings     
def collectTimeChanges(object):
    timeChanges = cmds.keyframe(object, query=True, tc=True)
    if timeChanges == None:
          timeChanges = 0
          uniqueKeyframes = []
    else:
          uniqueKeyframes = sorted(set(timeChanges))
    return uniqueKeyframes  


# returns keyframes of object and object's parents in an array
def findEffectingKeyframes(object):
    keyframeArray = []
    # collect time changes on object
    for i in collectTimeChanges(object):
          keyframeArray.append(i)

    for i in collectTransformInfluencers(object):
          for k in collectTimeChanges(i):
              keyframeArray.append(k)
    return sorted(set(keyframeArray))


# Collect Keyframe Data into a dictionary
def collectKeyframeData(currentObject):
    timeChanges = cmds.keyframe(currentObject, query=True, tc=True)
    #print "timeChanges: " + str(timeChanges)

    valueChanges = cmds.keyframe(currentObject, query=True, vc=True, at= ["translateX", "translateY", "translateZ", "rotateX", "rotateY", "rotateZ"])
    #print "valueChanges: " + str(valueChanges)

    if timeChanges == None:
        timeChanges = 0
        uniqueKeyframes = []
    else:
        uniqueKeyframes = sorted(set(timeChanges))
    #print "uniqueKeyframes: " + str(uniqueKeyframes)

    if valueChanges == None:
        valueChanges = []
        keyframeAmount = 0
    else:
        keyframeAmount = len(valueChanges)
    #print "length: " + str(keyframeAmount)
    
    # manage keyframe data into a dictionary
    keyframeDictionary = {}

    # create dictionary keys representing keyframes
    for i in range(len(uniqueKeyframes)):
        keyframeDictionary[uniqueKeyframes[i]] = []

    # append values of position data to keys
    for i in range(keyframeAmount):
         currentKeyframe = timeChanges[i]
         currentValue = valueChanges[i]
         #print "currentKeyframe: " + str(currentKeyframe) + " | currentValue: " + str(currentValue)
         keyframeDictionary[currentKeyframe].append(currentValue)

    return keyframeDictionary

def createOriginalAnimLocator(object):
    # create a corresponding locator - named "loc_object_originalAnim"
    locatorName = str("loc_" + str(object) + "_originalAnim")
    cmds.spaceLocator( n = locatorName)

    # parent constrain locator to object with offset off
    parentConstrainName = str(locatorName + "_parentConstrain")
    cmds.parentConstraint( object, locatorName, mo = 0, n = parentConstrainName )

    # bake locator translate and rotation animation based on first and last keyframe
    #get Start and End Frame of Time Slider
    keyframeArray = findEffectingKeyframes(object)
    endIteration = len(keyframeArray) - 1

    startFrame = keyframeArray[0]
    endFrame = keyframeArray[endIteration]

    cmds.bakeResults( locatorName, t=(startFrame, endFrame)) 

    # delete parent constrain on locator 
    cmds.delete(parentConstrainName)


# create locator and copy anim data
def copyAnimToLocator(object):
    keyframeList = findEffectingKeyframes(object)
    locatorName = "loc_" + str(object) + "_copyAnim"
    cmds.spaceLocator(n = locatorName)
    for i in keyframeList:
         cmds.currentTime(i, edit = True)
         constraintName = str(object) + "_currentFrame_parentConstraint"
         cmds.parentConstraint(object, locatorName, mo=0, name = constraintName)

         cmds.setKeyframe(locatorName, at="translateX")
         cmds.setKeyframe(locatorName, at="translateY")
         cmds.setKeyframe(locatorName, at="translateZ")
         cmds.setKeyframe(locatorName, at="rotateX")         
         cmds.setKeyframe(locatorName, at="rotateY")  
         cmds.setKeyframe(locatorName, at="rotateZ")  

         cmds.delete(constraintName)

def deleteAttributeKeys(object, attributeArray):
    keyframeDictionary = collectKeyframeData(object)
    for f in keyframeDictionary:
        currentFrame = int(f)
        for a in attributeArray:
             cmds.cutKey(object, time = (currentFrame, currentFrame), at = str(a))     

# deletes animation of object, copies to source object
def reanimateToObject(reanimatedObject,sourceAnimObject):
    sourceAnimKeyframes = findEffectingKeyframes(sourceAnimObject)
    keyedAttributes = ["translateX", "translateY", "translateZ", "rotateX", "rotateY", "rotateZ"]
    deleteAttributeKeys(reanimatedObject, keyedAttributes)

    for i in sourceAnimKeyframes:
         cmds.currentTime(i, edit = True)
         constraintName = str(reanimatedObject) + "_currentFrame_parentConstraint"
         cmds.parentConstraint(sourceAnimObject, reanimatedObject, mo=0, name = constraintName)

         cmds.setKeyframe(reanimatedObject, at="translateX")
         cmds.setKeyframe(reanimatedObject, at="translateY")
         cmds.setKeyframe(reanimatedObject, at="translateZ")
         cmds.setKeyframe(reanimatedObject, at="rotateX")         
         cmds.setKeyframe(reanimatedObject, at="rotateY")  
         cmds.setKeyframe(reanimatedObject, at="rotateZ")  

         cmds.delete(constraintName)

def reanimateObjects(objects):
    for i in objects:
        print "REANIMATING: " + str(i)
        currentLocator = "loc_" + str(i) + "_copyAnim"
        reanimateToObject(i, currentLocator)
        cmds.delete(currentLocator)

# Region: bake functions

#derive namespace based on selected orient
def defineNamespace(orient):
    orientString = str(orient)
    namespaceColonIndex = orientString.find(":")
    
    if namespaceColonIndex == -1:
          namespace = ""
          #print "no namespace"
    else:
          namespace = orientString[0:(namespaceColonIndex + 1)]
          # remove "[u'" before the namespace (weird unicode from cmds.ls(sl=True)
          namespace = namespace[3:namespaceColonIndex + 3]
    return namespace


# function: determine which limb controls need baking
def determineBake(control):
    worldAttribute = str(control) + ".world"
    if cmds.getAttr(worldAttribute) == 1:
        return objectsToBake.append(control)
    # check for animation on world space attribute:
    elif cmds.listConnections(worldAttribute, type='animCurve') != None:
        return objectsToBake.append(control)              
    else:
        print "skip " + worldAttribute


# Function: create locators that have world space animation data of objectsToBake
def createWorldLocators(objectsToBake):
    # cycle through each selected object
    for i in objectsToBake:
        createOriginalAnimLocator(i)
        copyAnimToLocator(i)
       

# Function: Transfer character animation to world space
def transferCharacterToWorld():
    createWorldLocators(objectsToBake)
    cmds.parent(orientControl, world = True)
    reanimateObjects(objectsToBake)


#VARIABLES
selected = cmds.ls(sl=True)
#print "selected: " + str(selected)


namespace = defineNamespace(selected)

# Region: Define controls
orientControl = namespace + "orient"
rootControl = namespace + "root_ctrl"
orientOffsetControl = namespace + "orient_offset"
legControlR = namespace + "leg_ctrl_R"
legControlL = namespace + "leg_ctrl_L"
armControlR = namespace + "arm_ctrl_R"
armControlL = namespace + "arm_ctrl_L"



# Region: Determine objects to bake
objectsToBake = [rootControl]

determineBake(legControlR)
determineBake(legControlL)
determineBake(armControlR)
determineBake(armControlL)


#print "objects to bake: " + str(objectsToBake)


#EXECUTE

transferCharacterToWorld()
