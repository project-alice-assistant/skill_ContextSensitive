from collections import deque
from pathlib import Path
from typing import Deque, Dict

from core.base.model.Intent import Intent
from core.base.model.AliceSkill import AliceSkill
from core.commons import constants
from core.dialog.model.DialogSession import DialogSession
from core.util.Decorators import IntentHandler


class ContextSensitive(AliceSkill):
	_INTENT_ANSWER_YES_OR_NO = Intent('AnswerYesOrNo')

	def __init__(self):
		self._history: Deque = deque(list(), 10)
		self._sayHistory: Dict[str, Deque] = dict()
		self._userSayHistory: Dict[str, Deque] = dict()
		super().__init__()


	@IntentHandler('DeleteThis')
	def deleteThisIntent(self, session: DialogSession):
		self.broadcast(method=constants.EVENT_CONTEXT_SENSITIVE_DELETE, exceptions=[self.name], propagateToSkills=True, session=session)


	@IntentHandler('EditThis')
	def editThisIntent(self, session: DialogSession):
		self.broadcast(method=constants.EVENT_CONTEXT_SENSITIVE_EDIT, exceptions=[self.name], propagateToSkills=True, session=session)


	@IntentHandler('RepeatThis')
	def repeatThisIntent(self, session: DialogSession):
		if 'Pronoun' in session.slots:
			if session.slotValue('Pronoun') == 'you':
				self.endDialog(session.sessionId, text=self.getLastChat(deviceUid=session.deviceUid))
			else:
				if self.ConfigManager.getAliceConfigByName('recordAudioAfterWakeword'):
					file = Path(self.AudioServer.SECOND_LAST_USER_SPEECH.format(session.user, session.deviceUid))
					if not file.exists():
						return

					self.playSound(file.stem, location=file.parent, deviceUid=session.deviceUid)
					self.endSession(sessionId=session.sessionId)
				else:
					self.endDialog(session.sessionId, text=self.getLastUserChat(deviceUid=session.deviceUid))
		else:
			self.endDialog(session.sessionId, text=self.getLastChat(deviceUid=session.deviceUid))


	def addToMessageHistory(self, session: DialogSession) -> bool:
		if session.message.topic in self.supportedIntents or session.intentName == str(self._INTENT_ANSWER_YES_OR_NO) or 'intent' not in session.intentName:
			return False

		try:
			customData = session.customData

			if 'user' not in customData:
				customData['user'] = session.user
				data = session.payload
				data['customData'] = customData
				session.payload = data

			self._history.append(session)

			return True
		except Exception as e:
			self.logError(f'Error adding to intent history: {e}')
			return False


	def lastSession(self) -> DialogSession:
		return self._history[-1]


	def addAliceChat(self, text: str, deviceUid: str):
		"""
		Saves what Alice says/speaks
		:param text: The text spoken
		:param deviceUid: Where it was spoken
		"""
		if deviceUid not in self._sayHistory:
			self._sayHistory[deviceUid] = deque(list(), 10)

		self._sayHistory[deviceUid].append(text)


	def addUserChat(self, text: str, deviceUid: str):
		"""
		Saves what a user says/asks
		:param text: The text that was captured
		:param deviceUid: Where it was captured
		"""
		if deviceUid not in self._userSayHistory:
			self._userSayHistory[deviceUid] = deque(list(), 10)

		self._userSayHistory[deviceUid].append(text)


	def getLastChat(self, deviceUid: str) -> str:
		return self._sayHistory[deviceUid][-1] if self._sayHistory.get(deviceUid) else self.randomTalk('nothing')


	def getLastUserChat(self, deviceUid: str) -> str:
		return self._userSayHistory[deviceUid][-2] if self._userSayHistory.get(deviceUid) else self.randomTalk('nothing')
