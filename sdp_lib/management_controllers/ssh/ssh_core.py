import asyncio
import os
import time
from typing import Iterator

import asyncssh

from api_v1.controller_management.schemas import AllowedControllers
from sdp_lib.management_controllers.fields_names import FieldsNames
from sdp_lib.management_controllers.hosts import Host
from sdp_lib.management_controllers.ssh.constants import kex_algs, enc_algs, term_type, proc_ssh_encoding, itc_login, \
    itc_passwd, stdout_encoding, stdout_decoding, swarco_r_login, swarco_r_passwd
from sdp_lib.utils_common import check_is_ipv4

access_levels = {
    'swarco_itc': (os.getenv('swarco_itc_login'), os.getenv('swarco_itc_passwd')),
    'swarco_r': (os.getenv('swarco_r_login'), os.getenv('swarco_r_passwd')),
    'peek_r': (os.getenv('peek_r_login'), os.getenv('peek_r_passwd')),
}


class AsyncConnectionSSH:

    def __init__(self,ip: str | None = None):
        self._ip = ip
        self._ssh_connection = None
        self._process = None

    def set_ip_or_none(self, ip: str):
        if check_is_ipv4(ip):
            self._ip = ip
        else:
            self._ip = None

    # @classmethod
    # def create_ssh_session(cls, ip_adress, access_level):
    #
    #     login, password = cls.access_levels.get(access_level)
    #
    #     client = paramiko.SSHClient()
    #     client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    #
    #     try:
    #         client.connect(hostname=ip_adress,
    #                        username=login,
    #                        password=password,
    #                        timeout=4,
    #                        look_for_keys=False, allow_agent=False)
    #         message = f'\n{datetime.today().strftime("%Y-%m-%d %H:%M:%S")} < Соединение установлено >'
    #     except paramiko.ssh_exception.NoValidConnectionsError as err:
    #         client = None
    #         message = f'\n{datetime.today().strftime("%Y-%m-%d %H:%M:%S")} Не удалось установить соединение с хостом...'
    #     except paramiko.ssh_exception.AuthenticationException as err:
    #         client = None
    #         message = f'\n{datetime.today().strftime("%Y-%m-%d %H:%M:%S")} Ошибка авторизации...'
    #     except TimeoutError as err:
    #         client = None
    #         message = f'\n{datetime.today().strftime("%Y-%m-%d %H:%M:%S")} Ошибка таймаута подключения...'
    #     except:
    #         client = None
    #         message = f'\n{datetime.today().strftime("%Y-%m-%d %H:%M:%S")} Программный сбой подключения...'
    #     return client, message

    @staticmethod
    async def read_timed(stream: asyncssh.SSHReader,
                         timeout: float = 1,
                         bufsize: int = 1024) -> str:
        """Read data from a stream with a timeout."""
        ret = ''
        while True:
            try:
                ret += await asyncio.wait_for(stream.read(bufsize), timeout)
            except (asyncio.TimeoutError, asyncio.CancelledError):
                return ret

    async def acreate_connection(
            self,
            username,
            password,
            login_timeout: float = 10,
            **kwargs
    ) -> str | None:
        """
        :param ip:
        :param username:
        :param password:
        :return: (None, asyncssh.connection.SSHClientConnection), если соедиенение успешно, иначе
                 (errorIndication, None)
        """
        errorIndication = None
        try:
            timeout = asyncssh.SSHClientConnectionOptions(login_timeout=login_timeout)
            self._ssh_connection = await asyncssh.connect(
                host=self._ip,
                username=username,
                password=password,
                options=timeout,
                kex_algs=kex_algs,
                encryption_algs=enc_algs,
                known_hosts=None,
                **kwargs
            )
        except asyncssh.misc.PermissionDenied:
            errorIndication = 'Permission denied'
        except (OSError, asyncssh.Error) as exc:
            errorIndication = 'SSH connection failed'
        except Exception as err:
            errorIndication = err
        return errorIndication

    async def acreate_proc(self, **kwargs):
        self._process = await self._ssh_connection.create_process(**kwargs)

    @property
    def ssh_connection(self):
        return self._ssh_connection

    @property
    def ssh_process(self):
        return self._process

    def close_conn(self):
        self._ssh_connection.close()



    @property
    def proc(self):
        return self._process


    # async def adownload_scp(self, access_level: str, files: list[str], dest_path: str = '.'):
    #     login, passwd = self.access_levels.get(access_level)
    #     errorIndication, conn = await self.acreate_connect(
    #         ip=self.ip_adress,
    #         username=login,
    #         password=passwd
    #     )
    #     if errorIndication:
    #         return errorIndication, [], self
    #     data = [(conn, file) for file in files]
    #
    #     dest_path = Path(self.reverse_slashes(f'{dest_path}/{self.ip_adress}/{self.set_curr_datetime(sep="-")}'))
    #
    #     if not os.path.exists(dest_path):
    #         os.makedirs(dest_path)
    #     else:
    #         await asyncio.sleep(0.5)
    #         os.makedirs(dest_path)
    #     try:
    #         await asyncssh.scp(data, dest_path)
    #         errorIndication = None
    #         return errorIndication, dest_path, self
    #     except (OSError, asyncssh.Error) as exc:
    #         errorIndication = 'SFTP operation failed: ' + str(exc)
    #         return errorIndication, dest_path, self
    #     except Exception as err:
    #         return err, (dest_path, os.listdir(dest_path)[-1]), self
    #     finally:
    #         conn.close()


class SwarcoConnectionSSH(AsyncConnectionSSH):

    def __init__(self, ip):
        super().__init__(ip=ip)

    async def acreate_connection(self, **kwargs):
        await super().acreate_connection(
            username=itc_login,
            password=itc_passwd,
            **kwargs
        )

    async def acreate_proc(self, **kwargs):
        await super().acreate_proc(term_type=term_type, encoding=proc_ssh_encoding, **kwargs)


class SwarcoSSH(Host):

    protocol = FieldsNames.protocol_snmp

    def __init__(self, ip=None, host_id=None, driver=None, ssh_conn=None, process=None):

        super().__init__(
            ipv4=ip, host_id=host_id, driver=driver
        )

        # if isinstance(driver, SwarcoConnectionSSH):
        #     self._ssh_conn = driver.ssh_connection
        #     self._process = driver.ssh_process

        self._ssh_conn = ssh_conn
        self._process = process


    async def send_commands(self, commands) -> tuple:
        """

        :param commands: Список комманд, которые будут отправлены в shell
        :return: errorIndication, stdout(вывод сеанса shell)
        """

        print(commands)

        # conn2 = AsyncConnectionSSH('10.179.108.177', AllowedControllers.SWARCO)
        # await conn2.acreate_connect(
        #     'itc',
        #     'level1NN'
        # )

        try:
            commands_for_json = []
            async with self._driver.create_process(term_type=term_type, encoding=proc_ssh_encoding) as proc:
                await self.read_timed(proc.stdout, timeout=3, bufsize=4096)
                for command in commands:
                    # logger.debug(command)
                    commands_for_json.append(command)
                    proc.stdin.write(command)
                response = await self.read_timed(proc.stdout, timeout=3, bufsize=4096)
                print(f'response: {response}')
                proc.stdin.write('exit\n')
                errorIndication, stdout = None, response
        except (OSError, asyncssh.Error):
            errorIndication = 'SSH connection failed'

    async def send_commands2(self, commands) -> tuple:
        """

        :param commands: Список комманд, которые будут отправлены в shell
        :return: errorIndication, stdout(вывод сеанса shell)
        """

        print(commands)

        # conn2 = AsyncConnectionSSH('10.179.108.177', AllowedControllers.SWARCO)
        # await conn2.acreate_connect(
        #     'itc',
        #     'level1NN'
        # )

        self.last_response = ''

        await self.driver.read_timed(self._process.stdout, timeout=3, bufsize=4096)
        for command in commands:
            self._process.stdin.write(f'{command}\n')

            response = await self.driver.read_timed(self._process.stdout, timeout=.5, bufsize=4096)
            self.last_response += response

            print(f'response: {response}')
        return self.last_response





async def main():

    conn = SwarcoConnectionSSH('10.179.108.177')
    await conn.acreate_connection()
    await conn.acreate_proc()



    obj = SwarcoSSH(ip=conn._ip, driver=conn, ssh_conn=conn.ssh_connection, process=conn.proc)
    #
    print(obj.driver)
    print(obj.driver.ssh_connection.is_closed())

    await obj.send_commands2(['lang UK', 'l2', '2727','SIMULATE DISPLAY --poll'])
    #
    # while True:
    #     print(f'obj.driver: {obj.driver}')
    #     print(f' obj.driver.is_closed(): {obj.driver.is_closed()}')
    #     print(f' proc.is_closing(): {proc.is_closing()}')
    #     a = input()
    #     if a == 'stop':
    #         break
    #     await obj.send_commands2(proc, a.split())
    # print(f' 1 >obj.driver: {obj.driver}')
    # print(f' 1 > obj.driver.is_closed(): {obj.driver.is_closed()}')
    # print(f' 1 > proc.is_closing(): {proc.is_closing()}')
    # # conn.close_conn()
    # await conn.aclose_conn()
    # print(f' 2 >obj.driver: {obj.driver}')
    # print(f' 2 > obj.driver.is_closed(): {obj.driver.is_closed()}')
    # print(f' 2 > proc.is_closing(): {proc.is_closing()}')
    # time.sleep(1)
    # print(f' 3 > obj.driver.is_closed(): {obj.driver.is_closed()}')

    print(f'obj.last_response: {obj.last_response}')
    print(f'obj.last_response: {obj.last_response.encode(stdout_encoding).decode(stdout_decoding)}')
    to_write = obj.last_response.encode(stdout_encoding).decode(stdout_decoding)
    print(f'type (obj.last_response): {type(to_write)}')
    with open('swarco_ssh_stdout.txt', 'w', encoding=stdout_encoding) as f:
        f.write(to_write)
if __name__ == '__main__':
    asyncio.run(main())




