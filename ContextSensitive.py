from collections import deque
from pathlib import Path
from typing import Deque, Dict

from core.base.model.Intent import Intent
from core.base.model.AliceSkill import AliceSkill
from core.commons import constants
from core.dialog.model.DialogSession import DialogSession
from core.util.Decorators import IntentHandler


class ContextSensitive(AliceSkill):
	_INTENT_ANSWER_YES_OR_NO = Intent('AnswerYesOrNo', isProtected=True)

	def __init__(self):
		self._history: Deque = deque(list(), 10)
		self._sayHistory: Dict[str, Deque] = dict()
		self._userSayHistory: Dict[str, Deque] = dict()
		self._userSpeech = Path(self.Commons.rootDir(), 'var/cache/userLastSpeech.wav')
		super().__init__()


	@IntentHandler('DeleteThis', isProtected=True)
	def deleteThisIntent(self, session: DialogSession):
		self.broadcast(method=constants.EVENT_CONTEXT_SENSITIVE_DELETE, exceptions=[self.name], propagateToSkills=True, session=session)


	@IntentHandler('EditThis', isProtected=True)
	def editThisIntent(self, session: DialogSession):
		self.broadcast(method=constants.EVENT_CONTEXT_SENSITIVE_EDIT, exceptions=[self.name], propagateToSkills=True, session=session)


	@IntentHandler('RepeatThis', isProtected=True)
	def repeatThisIntent(self, session: DialogSession):
		if 'Pronoun' in session.slots:
			if session.slotValue('Pronoun') == 'you':
				self.endDialog(session.sessionId, text=self.getLastChat(siteId=session.siteId))
			else:
				if self.ConfigManager.getAliceConfigByName('recordAudioAfterWakeword') and self._userSpeech:
					self.playSound(self._userSpeech.stem, location=Path('var/cache'), siteId=session.siteId)
					self.endSession(sessionId=session.sessionId)
				else:
					self.endDialog(session.sessionId, text=self.getLastUserChat(siteId=session.siteId))
		else:
			self.endDialog(session.sessionId, text=self.getLastChat(siteId=session.siteId))


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


	def addAliceChat(self, text: str, siteId: str):
		"""
		Saves what Alice says/speaks
		:param text: The text spoken
		:param siteId: Where it was spoken
		"""
		if siteId not in self._sayHistory:
			self._sayHistory[siteId] = deque(list(), 10)

		self._sayHistory[siteId].append(text)


	def addUserChat(self, text: str, siteId: str):
		"""
		Saves what a user says/asks
		:param text: The text that was captured
		:param siteId: Where it was captured
		"""
		if siteId not in self._userSayHistory:
			self._userSayHistory[siteId] = deque(list(), 10)

		self._userSayHistory[siteId].append(text)


	def getLastChat(self, siteId: str) -> str:
		return self._sayHistory[siteId][-1] if self._sayHistory.get(siteId) else self.randomTalk('nothing')


	def getLastUserChat(self, siteId: str) -> str:
		return self._userSayHistory[siteId][-2] if self._userSayHistory.get(siteId) else self.randomTalk('nothing')
