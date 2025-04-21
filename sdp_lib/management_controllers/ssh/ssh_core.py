import asyncio
import os
import time
import typing

import asyncssh
from asyncssh import SSHClientConnection, SSHClientProcess

from api_v1.controller_management.schemas import AllowedControllers
from sdp_lib.management_controllers.exceptions import ReadFromInteractiveShellError
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


async def read_timed(stream: asyncssh.SSHReader,
                     timeout: float = 1,
                     bufsize: int = 1024) -> str:
    """Read data from a stream with a timeout."""
    ret = ''
    print(f'in func read_timed')
    while True:
        try:
            # print(f'ret "u0000:"', '&&> \x00' in ret)
            # print(f'ret "u0000:"', '\u0000' in ret)
            # print(f'ret >> {ret}')
            # print(f'ret-----------------------:')
            ret += await asyncio.wait_for(stream.read(bufsize), timeout)
            ret = ret.replace('\u0000', '')
            # ret.strip().replace("&&> \u0000", '')
        except (asyncio.TimeoutError, asyncio.CancelledError):
            return ret
            # line.strip().replace("&&> \u0000", '') if line.startswith('&&') else line.strip()
            # return ret
            # print(f'ret: {ret}')
            # print(f'ret "u0000:"' , '&&> \x00' in ret)
            # print(f'ret "u0000:"' , '\u0000' in ret)
            # print(f'ret-----------------------:')
        # return ret

        # if cnt > 3 and not ret:
        #     raise ReadFromInteractiveShellError()

# class AsyncConnectionSSH:
#
#     def __init__(self,ip: str | None = None):
#         self._ip = ip
#         self._ssh_connection = None
#         self._process = None
#
#     def set_ip_or_none(self, ip: str):
#         if check_is_ipv4(ip):
#             self._ip = ip
#         else:
#             self._ip = None
#
#     # @classmethod
#     # def create_ssh_session(cls, ip_adress, access_level):
#     #
#     #     login, password = cls.access_levels.get(access_level)
#     #
#     #     client = paramiko.SSHClient()
#     #     client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
#     #
#     #     try:
#     #         client.connect(hostname=ip_adress,
#     #                        username=login,
#     #                        password=password,
#     #                        timeout=4,
#     #                        look_for_keys=False, allow_agent=False)
#     #         message = f'\n{datetime.today().strftime("%Y-%m-%d %H:%M:%S")} < Соединение установлено >'
#     #     except paramiko.ssh_exception.NoValidConnectionsError as err:
#     #         client = None
#     #         message = f'\n{datetime.today().strftime("%Y-%m-%d %H:%M:%S")} Не удалось установить соединение с хостом...'
#     #     except paramiko.ssh_exception.AuthenticationException as err:
#     #         client = None
#     #         message = f'\n{datetime.today().strftime("%Y-%m-%d %H:%M:%S")} Ошибка авторизации...'
#     #     except TimeoutError as err:
#     #         client = None
#     #         message = f'\n{datetime.today().strftime("%Y-%m-%d %H:%M:%S")} Ошибка таймаута подключения...'
#     #     except:
#     #         client = None
#     #         message = f'\n{datetime.today().strftime("%Y-%m-%d %H:%M:%S")} Программный сбой подключения...'
#     #     return client, message
#
#     @property
#     def host_ip(self):
#         return self._ip
#
#     @staticmethod
#     async def read_timed(stream: asyncssh.SSHReader,
#                          timeout: float = 1,
#                          bufsize: int = 1024) -> str:
#         """Read data from a stream with a timeout."""
#         ret = ''
#         while True:
#             try:
#                 ret += await asyncio.wait_for(stream.read(bufsize), timeout)
#             except (asyncio.TimeoutError, asyncio.CancelledError):
#                 return ret
#
#     async def acreate_connection(
#             self,
#             username,
#             password,
#             login_timeout: float = 10,
#             **kwargs
#     ) -> str | None:
#         """
#         :param ip:
#         :param username:
#         :param password:
#         :return: (None, asyncssh.connection.SSHClientConnection), если соедиенение успешно, иначе
#                  (errorIndication, None)
#         """
#         errorIndication = None
#         try:
#             timeout = asyncssh.SSHClientConnectionOptions(login_timeout=login_timeout,
#                                                           connect_timeout=4
#                                                           )
#             self._ssh_connection = await asyncssh.connect(
#                 host=self._ip,
#                 username=username,
#                 password=password,
#                 options=timeout,
#                 kex_algs=kex_algs,
#                 encryption_algs=enc_algs,
#                 known_hosts=None,
#                 **kwargs
#             )
#         except asyncssh.misc.PermissionDenied:
#             errorIndication = 'Permission denied'
#         except (OSError, asyncssh.Error) as exc:
#             errorIndication = 'SSH connection failed'
#         except Exception as err:
#             errorIndication = err
#         return errorIndication
#
#     async def acreate_proc(self, **kwargs):
#         self._process = await self._ssh_connection.create_process(**kwargs)
#
#     @property
#     def ssh_connection(self) -> SSHClientConnection:
#         return self._ssh_connection
#
#     @property
#     def ssh_process(self) -> SSHClientProcess:
#         return self._process
#
#     def close_conn(self):
#         self._ssh_connection.close()
#
#
#
#     # async def adownload_scp(self, access_level: str, files: list[str], dest_path: str = '.'):
#     #     login, passwd = self.access_levels.get(access_level)
#     #     errorIndication, conn = await self.acreate_connect(
#     #         ip=self.ip_adress,
#     #         username=login,
#     #         password=passwd
#     #     )
#     #     if errorIndication:
#     #         return errorIndication, [], self
#     #     data = [(conn, file) for file in files]
#     #
#     #     dest_path = Path(self.reverse_slashes(f'{dest_path}/{self.ip_adress}/{self.set_curr_datetime(sep="-")}'))
#     #
#     #     if not os.path.exists(dest_path):
#     #         os.makedirs(dest_path)
#     #     else:
#     #         await asyncio.sleep(0.5)
#     #         os.makedirs(dest_path)
#     #     try:
#     #         await asyncssh.scp(data, dest_path)
#     #         errorIndication = None
#     #         return errorIndication, dest_path, self
#     #     except (OSError, asyncssh.Error) as exc:
#     #         errorIndication = 'SFTP operation failed: ' + str(exc)
#     #         return errorIndication, dest_path, self
#     #     except Exception as err:
#     #         return err, (dest_path, os.listdir(dest_path)[-1]), self
#     #     finally:
#     #         conn.close()
# async with asyncssh.connect() as conn:
#     async with conn.create_process() as proc:


class SwarcoSSH(Host):

    protocol = FieldsNames.protocol_ssh

    def __init__(self, ip=None, host_id=None, driver: SSHClientConnection =None, process=None):

        super().__init__(
            ipv4=ip, host_id=host_id, driver=driver
        )
        self._ssh_process: SSHClientProcess = process
        self._success_conn_time = None
        self.raw_stdout = None

    async def create_connect(self, connect_timeout: float = 10, login_timeout: float = 10) -> SSHClientConnection:
        return await asyncssh.connect(
                    host=self._ipv4,
                    username=itc_login,
                    password=itc_passwd,
                    options=asyncssh.SSHClientConnectionOptions(connect_timeout=connect_timeout,
                                                                login_timeout=login_timeout),
                    kex_algs=kex_algs,
                    encryption_algs=enc_algs,
                    known_hosts=None,
            )

    async def create_proc(self, connection: SSHClientConnection) -> SSHClientProcess:
        return await connection.create_process(
            term_type=term_type,
            encoding=proc_ssh_encoding,
        )

    async def _send_commands(self, commands, parse=False):

        for command in commands:
            self._ssh_process.stdin.write(f'{command}\n')
            try:
                command_response = await read_timed(self._ssh_process.stdout, timeout=.5, bufsize=4096)
                self.raw_stdout.append((command, command_response))
            except ReadFromInteractiveShellError as exc:
                self.add_data_to_data_response_attrs(exc)
                break


    async def send_commands4(self, commands: list[str], *response_states) -> typing.Self:
        """

        :param commands: Список комманд, которые будут отправлены в shell
        :return: errorIndication, stdout(вывод сеанса shell)
        """

        print(commands)
        self.last_response = []
        self.raw_stdout = []
        try:
            self._driver = await self.create_connect()
            self._ssh_process = await self.create_proc(self._driver)
            await read_timed(self._ssh_process.stdout, timeout=.8, bufsize=4096)
            await self._send_commands(commands)
            need_parse_commands = self.get_commands_for_response_states(*response_states)
            await self._send_commands(commands)
            # if not self.response_errors:
            #     self.get_commands_for_response_states(*response_states):

                # await self._send_commands(*response_states)

            self.add_data_to_data_response_attrs(data={'pretty_output': self.last_response,
                                                       'raw_output': self.raw_stdout})
        except (OSError, asyncssh.Error):
            self.add_data_to_data_response_attrs('SSH connection failed')
        finally:
            # self._ssh_process.close()
            # self._ssh_process.terminate()
            # await self._ssh_process.wait()
            # await self._driver.wait_closed()
            # self._driver = None
            # self._ssh_process = None
            print(f'self.last_response send_commands4: {self.last_response}')
        return self

    def get_commands_for_response_states(self, states):
        matches = {
            'itc': ('itc', 'itc', None),
            'display': ('SIMULATE DISPLAY --poll', 'display', None),
        }
        commands = []
        for state in states:
            data = matches.get(state)
            if data is not None:
                command, fild_name, fn_handler = data
                commands.append(command)
            else:
                if 'instat' in state.lower():
                    commands.append((f'{state} ?', 'instat', None))
        return commands

    @property
    def process(self) -> SSHClientProcess:
        return self._ssh_process


async def main():
    connectt =None

    try:
        connectt = await asyncssh.connect(
            host='10.45.154.18',
            username=itc_login,
            password=itc_passwd,
            options=asyncssh.SSHClientConnectionOptions(login_timeout=10, connect_timeout=6),
            kex_algs=kex_algs,
            encryption_algs=enc_algs,
            known_hosts=None,
        )
        procx = await connectt.create_process(
            term_type=term_type,
                encoding=proc_ssh_encoding,)
        r = await read_timed(procx.stdout, timeout=.8, bufsize=4096)
        print(f'read_timed r :: {r}')
        rr = None
        while True:
            commands = input()
            if commands == 'stop':
                break

            commands = commands.split(';')
            for command in commands:
                procx.stdin.write(f'{command}\n')
                rr = await read_timed(procx.stdout, timeout=.5, bufsize=4096)
            print(f'read_timed rr :: {rr}')
            print('****' * 20)

        print(f'procx.stdout: {procx}')
        print(f'procx.stdout: {procx.stdout}')
        print('****' * 20)
        procx.kill()
        await procx.wait()

        procx = await connectt.create_process(
            term_type=term_type,
                encoding=proc_ssh_encoding,)
        await read_timed(procx.stdout, timeout=.8, bufsize=4096)

        print(f'procx.stdout: {procx.stdout}')
        print(f'procx.stdout: {procx}')
        print('****' * 20)


        print(f'connectt.is_closed(): {connectt.is_closed()}')
    except ValueError as exc:
        print(f'exc: + {exc}')
    finally:
        pass
        # await connectt.wait_closed()
    await asyncio.sleep(2)
    print(f'connectt: {connectt}')
    print(f'connectt.is_closed(): {connectt.is_closed()}')

    # obj = SwarcoSSH()
    # obj.set_ipv4('10.179.108.177')
    # await obj.create_connection()
    # await obj.create_process()



    # await obj.send_commands2(['lang UK', 'l2', '2727','SIMULATE DISPLAY --poll'])
    #
    # print(f'obj.last_response: {obj.last_response}')
    # to_write = obj.last_response.encode(stdout_encoding).decode(stdout_decoding)
    # print(f'type (obj.last_response): {type(to_write)}')
    # with open('swarco_ssh_stdout.txt', 'w') as f:
    #     f.write(to_write)
if __name__ == '__main__':
    asyncio.run(main())




