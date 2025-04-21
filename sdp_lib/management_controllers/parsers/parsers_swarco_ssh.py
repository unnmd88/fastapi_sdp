
from sdp_lib.management_controllers.ssh.swarco_terminal import ItcTerminal

def process_stdout_itc(content):
    return content

def process_stdout_instat(content):
    splited_stdout = content.splitlines()[1:-1]
    # return splited_stdout
    return [splited_stdout[3].replace(" ", '')[:9], splited_stdout[4].split(": ")[-1][:9]]


def process_stdoud_cbmem(content):
    return content

def process_stdoud_display(content):
    return content.splitlines()[1:-1]

itc_terminal = {
    ItcTerminal.itc_command: (ItcTerminal.field_name_itc, process_stdout_itc),
    ItcTerminal.display_command: (ItcTerminal.field_name_display, process_stdoud_display)
}



def process_terminal_stdout(command, content):
    r = itc_terminal.get(command)
    if r is not None:
        return r[0], r[1](content)

    if 'instat' in command.lower():
        return command.replace(' ?', ""), process_stdout_instat(content)
    elif 'cbmem' in command.lower():
        return command.replace(' ?', ""), process_stdoud_cbmem(content)

    return command, None

